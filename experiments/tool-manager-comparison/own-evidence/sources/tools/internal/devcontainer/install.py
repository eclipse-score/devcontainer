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

Dependency-free (stdlib only) provider orchestration, delegating native/Python
preparation to the shared provisioner. Bazel retains its pinned uvx launcher.

Usage:
  install.py install shellcheck yamlfmt
  install.py install-python pre-commit
  install.py version shellcheck
"""

# pyright: reportAny=false, reportUnusedCallResult=false, reportExplicitAny=false

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Container images copy the complete tools directory; source execution and
# Bazel runfiles use the same import root without installing a host package.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from score_tools.catalog import (
    LOCKFILE_ROOT,
    ToolData,
    _load_python_tools,
    all_definitions,
    apt_requirements,
    load_catalog_versions,
    load_environments,
    load_providers,
    validate_environment,
)
from score_tools.provision import host_platform, install_python, provision


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

    install_python(
        requirements,
        uv,
        bin_dir=Path(environment.get("UV_TOOL_BIN_DIR", Path.home() / ".local/bin")),
        tool_dir=Path(
            environment.get("UV_TOOL_DIR", Path.home() / ".local/share/uv/tools")
        ),
    )
    return 0


def _cmd_install(args: argparse.Namespace) -> int:
    """Compatibility entrypoint; the shared provisioner owns installation."""
    for tool in args.tools:
        if args.lockfile:
            _load_tool(args.lockfile, tool)
        provision(
            "native-" + tool,
            [tool],
            [],
            bin_dir=Path(args.destination),
            data_dir=Path(args.destination) / ".score-data",
            system=(args.os, args.cpu),
        )
    return 0


def _cmd_environment(args: argparse.Namespace) -> int:
    """Apply a named environment's native/Python selection in dependency order."""
    selection = validate_environment(
        args.environment,
        all_definitions(repository_metadata=False),
        platform="/".join(host_platform()),
    )
    if args.phase != "runtime":
        packages = [
            package
            for name in selection.get("build-apt", [])
            for package in load_providers()[name]["packages"]
        ]
        if packages:
            action = (
                ["install", "-y"]
                if args.phase == "build"
                else ["remove", "--purge", "-y"]
            )
            subprocess.run(["apt-get", *action, *packages], check=True)
        return 0
    # QEMU intentionally excludes recommendations; other packages retain the
    # distribution's normal dependency policy (including Python build headers).
    for recommends in (True, False):
        requirements = apt_requirements(args.environment, recommends=recommends)
        if requirements:
            flags = [] if recommends else ["--no-install-recommends"]
            subprocess.run(
                ["apt-get", "install", "-y", *flags, *requirements], check=True
            )
    provision(
        args.environment,
        selection["native"],
        selection["python"],
        bin_dir=Path(args.destination),
        data_dir=Path(args.tool_dir).parent / "score-packages",
    )
    for name in selection.get("npm", []):
        definition = load_providers()[name]
        subprocess.run(["npm", "install", "-g", definition["package"]], check=True)
    return 0


def _cmd_shell_metadata(args: argparse.Namespace) -> int:
    """Emit quoted data for the provider-specific feature setup, never shell code from definitions."""
    import re
    import shlex

    def emit(name, value):
        if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", name):
            raise SystemExit(f"Invalid metadata variable: {name}")
        if isinstance(value, dict):
            for key, child in value.items():
                emit(name + "_" + key, child)
        elif isinstance(value, str):
            print("export " + name + "=" + shlex.quote(value))

    for name, definition in load_providers().items():
        # Export only lifecycle setup inputs. Inventory metadata can use keys
        # such as linux/arm64 which deliberately are not shell identifiers.
        for field in ("version", "compatibility_version", "amd64", "arm64"):
            if field in definition:
                emit(name.replace("-", "_") + "_" + field, definition[field])
    # Python definitions are shared with Bazel and the installed uv package.
    for name, definition in _load_python_tools().items():
        emit(name.replace("-", "_"), definition)
    return 0


def _cmd_verify_environment(args: argparse.Namespace) -> int:
    """Inspect selected commands and installed Debian packages, not installer inputs."""
    import re

    selection = load_environments()[args.environment]
    versions = load_catalog_versions()
    observed = {}
    providers = load_providers()
    python_tools = _load_python_tools()
    for name in selection["native"] + selection["python"]:
        entrypoint = python_tools[name]["entrypoint"] if name in python_tools else name
        command = shutil.which(entrypoint)
        if command is None:
            raise SystemExit(f"Selected command missing from PATH: {name}")
        flag = "version" if name in ("starpls", "bazelisk") else "--version"
        environment = os.environ.copy()
        if name == "bazelisk":
            # Bazelisk's version command also launches Bazel. Bound this probe
            # to the declared image preinstall instead of resolving latest when
            # tests execute outside a workspace with a .bazelversion file.
            environment["USE_BAZEL_VERSION"] = providers["bazel"]["version"]
        run = subprocess.run(
            [command, flag],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            env=environment,
        )
        if run.returncode:
            raise SystemExit(
                f"Could not inspect {name} (exit {run.returncode}): {run.stdout}"
            )
        if not re.search(
            r"(?<![0-9.])" + re.escape(versions[name]) + r"(?![0-9.])", run.stdout
        ):
            raise SystemExit(f"Unexpected {name} version: {run.stdout}")
        observed[name] = {"command": command, "reported": run.stdout.strip()}
    for name in selection.get("apt", []):
        definition = providers[name]
        for entrypoint in definition.get("commands", []):
            if shutil.which(entrypoint) is None:
                raise SystemExit(
                    f"Selected APT command missing from PATH: {entrypoint}"
                )
        for module in definition.get("modules", []):
            subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import importlib, sys; importlib.import_module(sys.argv[1])",
                    module,
                ],
                check=True,
            )
        for package in definition["packages"]:
            package = package.format(version=definition.get("version", ""))
            run = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}\\n${Version}", package],
                text=True,
                stdout=subprocess.PIPE,
                check=True,
            )
            status, version = run.stdout.splitlines()
            if status != "install ok installed":
                raise SystemExit(f"Selected package is not installed: {package}")
            if definition["policy"] == "prefix" and not version.startswith(
                definition["version"]
            ):
                raise SystemExit(f"Unexpected {package} version: {version}")
            observed[package] = {"resolved": version, "policy": definition["policy"]}
    for name in selection.get("npm", []):
        definition = providers[name]
        run = subprocess.run(
            ["npm", "list", "--global", "--depth=0", "--json"],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        )
        installed = (
            json.loads(run.stdout).get("dependencies", {}).get(definition["package"])
        )
        if installed is None or not installed.get("version"):
            raise SystemExit(f"Selected npm package missing: {definition['package']}")
        for entrypoint in definition.get("commands", []):
            if shutil.which(entrypoint) is None:
                raise SystemExit(
                    f"Selected npm command missing from PATH: {entrypoint}"
                )
        observed[name] = {
            "resolved": installed["version"],
            "policy": definition["policy"],
        }
    for name in selection.get("build-apt", []):
        for package in providers[name]["packages"]:
            run = subprocess.run(
                ["dpkg-query", "-W", "-f=${Status}", package],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if run.returncode == 0 and run.stdout == "install ok installed":
                raise SystemExit(f"Temporary build package was not removed: {package}")
    print(json.dumps(observed, indent=2))
    return 0


def _cmd_selected(args: argparse.Namespace) -> int:
    """Return whether a tool is selected, for provider-specific lifecycle setup."""
    selections = load_environments()[args.environment]
    return 0 if any(args.tool in names for names in selections.values()) else 1


def _cmd_items(args: argparse.Namespace) -> int:
    """Expose a provider-owned bundle list to lifecycle setup and verification."""
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

    items_parser = subparsers.add_parser(
        "items", help="Read a provider bundle's owned members."
    )
    items_parser.add_argument("tool")
    items_parser.add_argument("field")
    items_parser.set_defaults(func=_cmd_items)

    selected_parser = subparsers.add_parser(
        "selected", help="Query environment membership for special setup."
    )
    selected_parser.add_argument("environment")
    selected_parser.add_argument("tool")
    selected_parser.set_defaults(func=_cmd_selected)

    verify_parser = subparsers.add_parser(
        "verify-environment", help="Inspect actual installed selections."
    )
    verify_parser.add_argument("environment")
    verify_parser.set_defaults(func=_cmd_verify_environment)

    metadata_parser = subparsers.add_parser(
        "shell-metadata", help="Read feature setup metadata."
    )
    metadata_parser.set_defaults(func=_cmd_shell_metadata)

    environment_parser = subparsers.add_parser(
        "environment", help="Install a declared environment selection."
    )
    environment_parser.add_argument("environment")
    environment_parser.add_argument(
        "--phase", choices=("runtime", "build", "cleanup"), default="runtime"
    )
    environment_parser.add_argument("--destination", default="/usr/local/bin")
    environment_parser.add_argument("--tool-dir", default="/usr/local/share/uv/tools")
    environment_parser.set_defaults(func=_cmd_environment)

    install_parser = subparsers.add_parser(
        "install",
        help="Download, verify, and install tools.",
    )
    install_parser.add_argument("tools", nargs="+")
    install_parser.add_argument("--lockfile")
    install_parser.add_argument("--destination", default="/usr/local/bin")
    install_parser.add_argument("--os", default=host_platform()[0])
    install_parser.add_argument("--cpu", default=host_platform()[1])
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
