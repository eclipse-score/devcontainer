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
  install.py install-python pre-commit
  install.py version shellcheck
"""

# pyright: reportAny=false, reportUnusedCallResult=false, reportExplicitAny=false

from __future__ import annotations

import argparse
import ast
import hashlib
import json
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
from typing import NotRequired, TypedDict
from collections.abc import Iterator


class Binary(TypedDict):
    """A single binary entry from a tool's lockfile definition."""

    os: str
    cpu: str
    kind: str
    url: str
    sha256: str
    type: NotRequired[str]
    file: NotRequired[str]
    dir: NotRequired[str]


class ToolData(TypedDict):
    """Tool metadata from a lockfile entry."""

    version: NotRequired[str]
    description: NotRequired[str]
    binaries: list[Binary]


LOCKFILE_ROOT = Path(__file__).resolve().parents[2] / "lockfiles"
PYTHON_TOOL_CATALOG = LOCKFILE_ROOT / "python_tools.bzl"


class PythonTool(TypedDict):
    """Metadata shared by the container installer and Bazel launcher."""

    # The distribution and console entrypoint can have different names.
    package: str
    version: str
    entrypoint: str
    # User-facing text is kept beside the pin so generated docs cannot drift.
    description: str


def _iter_catalog() -> Iterator[tuple[str, str, ToolData]]:
    """Yield (tool, lockfile filename, definition) for every catalog entry."""
    for path in sorted(LOCKFILE_ROOT.glob("*.lock.json")):
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)

        for tool, definition in data.items():
            if tool.startswith("$"):
                continue
            if not isinstance(definition, dict):
                raise SystemExit(f"Unexpected entry '{tool}' in '{path.name}'")
            yield tool, path.name, definition


def _parse_python_tool_catalog() -> object:
    """Return the literal assigned to ``PYTHON_TOOLS``.

    The feature installer runs as root, so importing or executing a repository
    file would cross a privilege boundary. Parsing one assignment and accepting
    only literal data lets Bazel and the installer share a catalog safely.
    """
    try:
        module = ast.parse(
            PYTHON_TOOL_CATALOG.read_text(encoding="utf-8"),
            filename=str(PYTHON_TOOL_CATALOG),
        )
    except SyntaxError as exc:
        raise SystemExit(f"Malformed Python tool catalog: {exc}") from exc

    # Exactly one statement preserves the catalog's data-only contract.
    if len(module.body) != 1:
        raise SystemExit(
            "Python tool catalog must contain only a PYTHON_TOOLS assignment"
        )

    assignment = module.body[0]
    if not isinstance(assignment, ast.Assign) or len(assignment.targets) != 1:
        raise SystemExit(
            "Python tool catalog must contain only a PYTHON_TOOLS assignment"
        )

    target = assignment.targets[0]
    if not isinstance(target, ast.Name) or target.id != "PYTHON_TOOLS":
        raise SystemExit("Python tool catalog must assign its data to PYTHON_TOOLS")

    try:
        return ast.literal_eval(assignment.value)
    except (TypeError, ValueError) as exc:
        raise SystemExit("Python tool catalog must contain only literal data") from exc


def _load_python_tools() -> dict[str, PythonTool]:
    """Validate the shared catalog and return typed Python tool metadata."""
    catalog = _parse_python_tool_catalog()
    if not isinstance(catalog, dict):
        raise SystemExit("PYTHON_TOOLS must be a dictionary")

    tools: dict[str, PythonTool] = {}
    for command, metadata in catalog.items():
        if (
            not isinstance(command, str)
            or not command
            or not isinstance(metadata, dict)
        ):
            raise SystemExit(f"Malformed Python tool catalog entry for '{command}'")

        package = metadata.get("package")
        version = metadata.get("version")
        entrypoint = metadata.get("entrypoint")
        description = metadata.get("description")
        # Central validation gives Bazel, installation, and documentation the
        # same required-field contract.
        if not all(
            isinstance(value, str) and value
            for value in (package, version, entrypoint, description)
        ):
            raise SystemExit(f"Malformed Python tool catalog entry for '{command}'")

        tools[command] = {
            "package": package,
            "version": version,
            "entrypoint": entrypoint,
            "description": description,
        }
    return tools


def load_catalog_versions() -> dict[str, str]:
    """Return every tool version declared by the lockfile catalog."""
    versions: dict[str, str] = {}

    for tool, filename, definition in _iter_catalog():
        version = definition.get("version")
        if not isinstance(version, str):
            raise SystemExit(
                f"Tool '{tool}' in '{filename}' does not define a string version"
            )
        if tool in versions:
            raise SystemExit(f"Tool '{tool}' is defined by multiple lockfiles")
        versions[tool] = version

    for tool, definition in _load_python_tools().items():
        if tool in versions:
            raise SystemExit(f"Tool '{tool}' is defined by multiple catalogs")
        versions[tool] = definition["version"]

    return versions


def load_catalog_descriptions() -> dict[str, str]:
    """Return every tool description declared by the lockfile catalog.

    Tools without a description are omitted so callers can report a
    friendly list of undocumented tools instead of failing on the first
    one encountered.
    """
    descriptions: dict[str, str] = {}

    for tool, filename, definition in _iter_catalog():
        description = definition.get("description")
        if description is None:
            continue
        if not isinstance(description, str):
            raise SystemExit(
                f"Tool '{tool}' in '{filename}' has a non-string description"
            )
        if tool in descriptions:
            raise SystemExit(f"Tool '{tool}' is defined by multiple lockfiles")
        descriptions[tool] = description

    for tool, definition in _load_python_tools().items():
        if tool in descriptions:
            raise SystemExit(f"Tool '{tool}' is defined by multiple catalogs")
        descriptions[tool] = definition["description"]

    return descriptions


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


def _lockfile_path(lockfile: str) -> Path:
    """Resolve a lockfile basename like `ruff` to `ruff.lock.json`."""
    return LOCKFILE_ROOT / f"{lockfile}.lock.json"


def _load_tool(lockfile: str, tool: str) -> ToolData:
    """Load one tool entry from a lockfile and fail with a clear message."""
    with _lockfile_path(lockfile).open(encoding="utf-8") as handle:
        data = json.load(handle)

    try:
        return data[tool]
    except KeyError as exc:
        raise SystemExit(
            f"Tool '{tool}' not found in lockfile '{lockfile}.lock.json'",
        ) from exc


def _find_lockfile(tool: str) -> str:
    """Find the lockfile basename that declares a tool."""
    for path in sorted(LOCKFILE_ROOT.glob("*.lock.json")):
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if tool in data:
            return path.name.removesuffix(".lock.json")

    raise SystemExit(f"Tool '{tool}' not found in lockfile catalog")


def _resolve_lockfile(tool: str, lockfile: str | None = None) -> str:
    """Return the lockfile basename for *tool*, auto-detecting when needed."""
    if lockfile is not None:
        return lockfile
    if _lockfile_path(tool).exists():
        return tool
    return _find_lockfile(tool)


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

    args.lockfile = _resolve_lockfile(args.tool, args.lockfile)
    tool_data = _load_tool(args.lockfile, args.tool)
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
    catalog = _load_python_tools()
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

    for tool in args.tools:
        lockfile = _resolve_lockfile(tool, args.lockfile)
        tool_data = _load_tool(lockfile, tool)
        binary = _select_binary(tool_data, args.os, args.cpu)

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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install pinned tools from multitool-compatible lockfiles.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

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

    install_python_parser = subparsers.add_parser(
        "install-python",
        help="Install Python command-line tools declared in python_tools.bzl.",
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
