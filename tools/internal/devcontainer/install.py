#!/usr/bin/env python3
# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Install pinned tools from the shared `tools/lockfiles` catalog.

Dependency-free (stdlib only) so feature installers can use the Python already
present in the image. Bazel executes Python tools through a shell launcher and
the pinned uvx runtime, keeping this installer container-specific.

Usage:
  install.py install shellcheck yamlfmt
  install.py install-environment s-core-local
  install.py install-python pre-commit
  install.py version shellcheck
"""

# pyright: reportAny=false, reportUnusedCallResult=false, reportExplicitAny=false

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

# Resolve from this file, not cwd, for direct execution and copied tools trees.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from catalog import (
    Binary,
    ToolData,
    all_definitions,
    apt_requirements,
    load_catalog_versions,
    load_environments,
    load_python_tools,
    load_providers,
    load_setup_metadata,
    load_tool,
    resolve_lockfile,
)


def _detect_os() -> str:
    """Map Python's platform string to the lockfile schema's OS names."""
    system = platform.system()
    if system == "Linux":
        return "linux"
    if system == "Darwin":
        return "macos"
    raise SystemExit(f"Unsupported OS: {system}")


def _detect_cpu() -> str:
    """Map Python's machine string to the lockfile schema's CPU names."""
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    raise SystemExit(f"Unsupported CPU architecture: {machine}")


def _select_binary(tool_data: ToolData, os_name: str, cpu: str) -> Binary:
    """Pick the binary entry matching the requested platform."""
    for binary in tool_data["binaries"]:
        if binary["os"] == os_name and binary["cpu"] == cpu:
            return binary

    raise SystemExit(
        f"No binary defined for os={os_name!r}, cpu={cpu!r}",
    )


def _cmd_version(args: argparse.Namespace) -> int:
    """Print the declared version for one tool."""
    if args.lockfile is None:
        versions = load_catalog_versions()
        try:
            print(versions[args.tool])
        except KeyError as exc:
            raise SystemExit(
                f"Tool '{args.tool}' not found in lockfile catalog"
            ) from exc
        return 0

    args.lockfile = resolve_lockfile(args.tool, args.lockfile)
    tool_data = load_tool(args.lockfile, args.tool)
    version = tool_data.get("version")
    if version is None:
        raise SystemExit(
            f"Tool '{args.tool}' in '{args.lockfile}.lock.json' does not define a version",
        )
    print(version)
    return 0


def _cmd_install_python(args: argparse.Namespace) -> int:
    """Install catalogued Python CLIs into the DevContainer with pinned uv."""
    # Resolve uv from PATH by default so feature scripts use the binary already
    # installed from uv.lock.json, while tests can inject a controlled binary.
    uv = shutil.which(args.uv)
    if uv is None:
        raise SystemExit(
            f"Could not install Python tools: '{args.uv}' was not found on PATH"
        )

    # Fixed system paths make feature installs independent of the root account's
    # uv defaults and expose the entrypoints to every container user.
    environment = os.environ.copy()
    if args.bin_dir is not None:
        environment["UV_TOOL_BIN_DIR"] = args.bin_dir
    if args.tool_dir is not None:
        environment["UV_TOOL_DIR"] = args.tool_dir

    # Resolve every requested name before changing the filesystem. A typo in a
    # later argument must not leave the container with a partially applied set.
    catalog = load_python_tools()
    requirements: list[str] = []
    for tool in args.tools:
        try:
            tool_data = catalog[tool]
        except KeyError as exc:
            raise SystemExit(f"Tool '{tool}' not found in Python tool catalog") from exc
        requirements.append(f"{tool_data['package']}=={tool_data['version']}")

    for requirement in requirements:
        # --force reapplies the catalog pin when a persistent layer already
        # contains another version, making container rebuilds deterministic.
        subprocess.run(
            [uv, "tool", "install", "--force", requirement],
            check=True,
            env=environment,
        )
    return 0


def _place_binary(source: Path, destination: Path) -> None:
    """Copy a file to its destination with executable permissions."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    destination.chmod(0o755)


def _extract_member(
    binary: Binary, archive_path: Path, out_path: Path, tool: str
) -> None:
    """Extract one member from an archive and write it to *out_path*."""
    archive_type = binary.get("type", "")
    member = binary.get("file")
    if member is None:
        raise SystemExit(f"Binary entry for {tool} does not define 'file' field")

    if archive_type in ("tar.gz", "tgz", "tar.xz", "txz"):
        with tarfile.open(archive_path) as tf:
            reader = tf.extractfile(member)
            if reader is None:
                raise SystemExit(f"Cannot extract '{member}' from archive for {tool}")
            out_path.write_bytes(reader.read())
    elif archive_type == "zip":
        with zipfile.ZipFile(archive_path) as zf:
            out_path.write_bytes(zf.read(member))
    else:
        raise SystemExit(f"Unsupported archive type '{archive_type}' for {tool}")


def _extract_dir(binary: Binary, archive_path: Path, out_dir: Path, tool: str) -> None:
    """Extract a directory from a tar archive, stripping the top-level prefix."""
    dir_prefix = binary.get("dir")
    if dir_prefix is None:
        raise SystemExit(f"Binary entry for {tool} does not define 'dir' field")
    prefix = dir_prefix.rstrip("/") + "/"

    try:
        with tarfile.open(archive_path) as tf:
            for member in tf.getmembers():
                if not member.name.startswith(prefix):
                    continue
                rel = member.name[len(prefix) :]
                if not rel:
                    continue
                dest = out_dir / rel
                if member.isdir():
                    dest.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    reader = tf.extractfile(member)
                    if reader is not None:
                        dest.write_bytes(reader.read())
                    if member.mode & 0o111:
                        dest.chmod(dest.stat().st_mode | 0o111)
    except tarfile.TarError as exc:
        raise SystemExit(f"Failed to extract tar archive for {tool}: {exc}") from exc


def _cmd_install(args: argparse.Namespace) -> int:
    """Download, verify, and install tools from the lockfile catalog."""
    dest_dir = Path(args.destination)

    # Check every requested tool has a download for this OS and CPU first.
    # A bad name late in the list must not leave earlier tools installed.
    binaries: list[tuple[str, Binary]] = []
    for tool in args.tools:
        lockfile = resolve_lockfile(tool, args.lockfile)
        tool_data = load_tool(lockfile, tool)
        try:
            binary = _select_binary(tool_data, args.os, args.cpu)
        except SystemExit as exc:
            raise SystemExit(f"Tool '{tool}': {exc}") from exc
        binaries.append((tool, binary))

    for tool, binary in binaries:
        kind = binary["kind"]
        url = binary["url"]
        expected_sha256 = binary["sha256"]
        destination = dest_dir / tool

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            download = tmp / "download"

            urllib.request.urlretrieve(url, download)

            actual = hashlib.sha256(download.read_bytes()).hexdigest()
            if actual != expected_sha256:
                raise SystemExit(
                    f"Checksum mismatch for {tool}: "
                    + f"expected {expected_sha256}, got {actual}"
                )

            if kind == "file":
                _place_binary(download, destination)
            elif kind == "archive":
                if "dir" in binary:
                    extracted_dir = tmp / "extracted_dir"
                    extracted_dir.mkdir()
                    _extract_dir(binary, download, extracted_dir, tool)
                    shutil.copytree(
                        str(extracted_dir), str(dest_dir), dirs_exist_ok=True
                    )
                    destination.chmod(0o755)
                else:
                    extracted = tmp / "extracted"
                    _extract_member(binary, download, extracted, tool)
                    if extracted.exists():
                        _place_binary(extracted, destination)
            else:
                raise SystemExit(f"Unsupported kind '{kind}' for {tool}")

    return 0


def _is_writable(path: str) -> bool:
    """Check the nearest existing parent when an install directory is still missing."""
    directory = Path(path).resolve()
    while not directory.exists():
        directory = directory.parent
    return os.access(directory, os.W_OK)


def _delegate_system_installation(
    args: argparse.Namespace, selection: dict[str, list[str]], setup_scripts: list[Path]
) -> bool:
    """Return whether system installation was completed by a privileged child."""
    if os.geteuid() == 0:
        return False
    providers = [
        provider
        for provider in args.providers
        if provider != "npm"
        and (selection.get(provider) or (provider == "setup" and setup_scripts))
    ]
    if args.phase != "runtime":
        providers = ["apt"]
        needs_root = bool(selection.get("build-apt"))
    else:
        needs_root = (
            any(provider in providers for provider in ("apt", "setup"))
            or ("native" in providers and not _is_writable(args.destination))
            or (
                "python" in providers
                and not all(_is_writable(p) for p in (args.destination, args.tool_dir))
            )
        )
    if not needs_root:
        return False

    # Reuse the same installer and explicit paths under sudo. Do not elevate the
    # whole invocation: npm must retain the user's PATH and global package prefix.
    subprocess.run(
        [
            "sudo",
            sys.executable,
            str(Path(__file__).resolve()),
            "install-environment",
            args.environment,
            "--phase",
            args.phase,
            "--destination",
            str(Path(args.destination).resolve()),
            "--tool-dir",
            str(Path(args.tool_dir).resolve()),
            "--os",
            args.os,
            "--cpu",
            args.cpu,
            "--providers",
            *providers,
        ],
        check=True,
    )
    return True


def _cmd_install_environment(args: argparse.Namespace) -> int:
    """Install an environment's tools, or add/remove its temporary build packages."""
    selection = load_environments().get(args.environment)
    if selection is None:
        raise SystemExit(f"Unknown tool environment '{args.environment}'")
    definitions = all_definitions()
    system = args.os + "/" + args.cpu
    # Even the build phase checks tools needed by the finished image. Report
    # missing downloads before installing packages used only during setup.
    for names in selection.values():
        for name in names:
            definition = definitions[name]
            if definition["provider"] == "native":
                try:
                    _select_binary(definition, args.os, args.cpu)
                except SystemExit as exc:
                    raise SystemExit(f"Tool '{name}': {exc}") from exc
            elif definition["provider"] in ("apt", "release", "bazelisk"):
                if system not in definition[
                    "platforms"
                ] and system not in definition.get("omissions", {}):
                    raise SystemExit(f"Tool '{name}' is unsupported on {system}")

    # Some tools need extra configuration, such as setting JAVA_HOME. Only
    # setup scripts shipped next to this installer can be selected.
    setup_scripts = []
    setup_root = Path(__file__).resolve().parent / "setup"
    for name in selection.get("apt", []) + selection.get("setup", []):
        definition = definitions[name]
        script = definition.get("setup_script")
        if script is None:
            continue
        if Path(script).name != script or not (setup_root / script).is_file():
            raise SystemExit(f"Invalid setup script for '{name}': {script}")
        if system not in definition.get("omissions", {}):
            setup_scripts.append(setup_root / script)

    if args.phase == "all":
        phases = ("build", "runtime", "cleanup")
        if not {"apt", "setup"}.intersection(args.providers):
            phases = ("runtime",)
        for phase in phases:
            phase_args = argparse.Namespace(**vars(args))
            phase_args.phase = phase
            _apply_environment(phase_args, selection, definitions, setup_scripts)
        return 0
    return _apply_environment(args, selection, definitions, setup_scripts)


def _apply_environment(args, selection, definitions, setup_scripts) -> int:
    """Apply one validated installation phase, elevating system steps when needed."""
    if args.phase != "runtime" and not {"apt", "setup"}.intersection(args.providers):
        return 0
    if _delegate_system_installation(args, selection, setup_scripts):
        if args.phase != "runtime":
            return 0
        # System groups are complete; npm still runs with the caller's Node setup.
        args.providers = [p for p in args.providers if p == "npm"]

    # Build packages, such as zstd for unpacking CodeQL, are added before tool
    # installation and removed after all setup steps have finished.
    if args.phase != "runtime":
        packages = [
            package
            for name in selection.get("build-apt", [])
            for package in definitions[name]["packages"]
        ]
        if packages:
            action = (
                ["install", "-y"]
                if args.phase == "build"
                else ["remove", "--purge", "-y"]
            )
            subprocess.run(["apt-get", *action, *packages], check=True)
        return 0

    # APT normally installs recommended extra packages. QEMU opts out; the
    # other packages keep that default, including Python build dependencies.
    for recommends in (True, False) if "apt" in args.providers else ():
        packages = apt_requirements(selection, definitions, recommends=recommends)
        if packages:
            flags = [] if recommends else ["--no-install-recommends", "--fix-broken"]
            subprocess.run(["apt-get", "install", "-y", *flags, *packages], check=True)
    # Install uv as a native tool before using it to install Python tools.
    if "native" in args.providers:
        args.tools = selection.get("native", [])
        args.lockfile = None
        _cmd_install(args)
    if "python" in args.providers and selection.get("python"):
        args.tools = selection["python"]
        args.uv = str(Path(args.destination).resolve() / "uv")
        args.bin_dir = args.destination
        _cmd_install_python(args)
    for name in selection.get("npm", []) if "npm" in args.providers else ():
        subprocess.run(
            ["npm", "install", "-g", definitions[name]["package"]], check=True
        )
    # Pass variables to the setup processes. Python cannot change the
    # environment of the shell that launched this installer.
    if "setup" in args.providers and setup_scripts:
        environment = {**os.environ, **load_setup_metadata()}
        environment["SCORE_TOOL_ENVIRONMENT"] = args.environment
        environment["SCORE_TOOLS_INSTALLER"] = str(Path(__file__).resolve())
        for script in setup_scripts:
            subprocess.run(["bash", str(script)], check=True, env=environment)
    return 0


def _cmd_shell_metadata(args: argparse.Namespace) -> int:
    """Print shell-quoted exports so feature tests can read versions in their shell."""
    import shlex

    for name, value in load_setup_metadata().items():
        print("export " + name + "=" + shlex.quote(value))
    return 0


def _cmd_selected(args: argparse.Namespace) -> int:
    """Exit with 0 if the environment selects this tool, or 1 if it does not."""
    selections = load_environments()[args.environment]
    return 0 if any(args.tool in names for names in selections.values()) else 1


def _cmd_items(args: argparse.Namespace) -> int:
    """Print a tool definition's list, such as CodeQL packs, one item per line."""
    value = load_providers()[args.tool][args.field]
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item or "\n" in item for item in value)
    ):
        raise SystemExit(
            f"{args.tool}/{args.field} must be a non-empty list of single-line strings"
        )
    print("\n".join(value))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install pinned tools from multitool-compatible lockfiles.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata_parser = subparsers.add_parser(
        "shell-metadata", help="Read feature setup metadata."
    )
    metadata_parser.set_defaults(func=_cmd_shell_metadata)
    selected_parser = subparsers.add_parser(
        "selected", help="Query membership for feature-specific setup."
    )
    selected_parser.add_argument("environment")
    selected_parser.add_argument("tool")
    selected_parser.set_defaults(func=_cmd_selected)
    items_parser = subparsers.add_parser("items", help="Read a setup bundle's members.")
    items_parser.add_argument("tool")
    items_parser.add_argument("field")
    items_parser.set_defaults(func=_cmd_items)

    install_parser = subparsers.add_parser(
        "install",
        help="Download, verify, and install tools.",
    )
    install_parser.add_argument("tools", nargs="+")
    install_parser.add_argument("--lockfile")
    install_parser.add_argument("--destination", default="/usr/local/bin")
    install_parser.add_argument("--os", default=_detect_os())
    install_parser.add_argument("--cpu", default=_detect_cpu())
    install_parser.set_defaults(func=_cmd_install)

    environment_parser = subparsers.add_parser(
        "install-environment",
        help="Apply a tool selection from tools/environments.json.",
    )
    environment_parser.add_argument("environment")
    environment_parser.add_argument(
        "--providers",
        nargs="+",
        choices=("apt", "native", "python", "npm", "setup"),
        default=("apt", "native", "python", "npm", "setup"),
        help="Apply only these provider groups; installation rights are handled automatically.",
    )
    environment_parser.add_argument(
        "--phase",
        choices=("all", "runtime", "build", "cleanup"),
        default="all",
        help="Run all installation phases by default, or apply just one phase.",
    )
    environment_parser.add_argument("--tool-dir", default="/usr/local/share/uv/tools")
    environment_parser.add_argument("--destination", default="/usr/local/bin")
    environment_parser.add_argument("--os", default=_detect_os())
    environment_parser.add_argument("--cpu", default=_detect_cpu())
    environment_parser.set_defaults(func=_cmd_install_environment)

    install_python_parser = subparsers.add_parser(
        "install-python",
        help="Install Python command-line tools declared in providers.json.",
    )
    install_python_parser.add_argument(
        "tools",
        nargs="+",
        help="Catalog command names to install.",
    )
    install_python_parser.add_argument(
        "--uv",
        default="uv",
        help="uv executable installed from the native tool lockfile.",
    )
    install_python_parser.add_argument(
        "--bin-dir",
        help="Directory in which uv exposes console entrypoints.",
    )
    install_python_parser.add_argument(
        "--tool-dir",
        help="Directory in which uv stores isolated tool environments.",
    )
    install_python_parser.set_defaults(func=_cmd_install_python)

    version_parser = subparsers.add_parser(
        "version",
        help="Print the declared version for a tool.",
    )
    version_parser.add_argument("tool")
    version_parser.add_argument("--lockfile")
    version_parser.set_defaults(func=_cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
