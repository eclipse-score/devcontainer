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
"""Install pinned tools from the `tools/lockfiles/*.lock.json` catalog.

Dependency-free (stdlib only) so devcontainer feature installers can use it
without extra packages.

Usage:
  tool_installer.py install shellcheck yamlfmt
  tool_installer.py version shellcheck
"""

# pyright: reportAny=false, reportUnusedCallResult=false, reportExplicitAny=false

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import NotRequired, TypedDict


class Binary(TypedDict):
    """A single binary entry from a tool's lockfile definition."""

    os: str
    cpu: str
    kind: str
    url: str
    sha256: str
    type: NotRequired[str]
    file: NotRequired[str]


class ToolData(TypedDict):
    """Tool metadata from a lockfile entry."""

    version: NotRequired[str]
    binaries: list[Binary]


LOCKFILE_ROOT = Path(__file__).resolve().parent / "lockfiles"


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
    args.lockfile = _resolve_lockfile(args.tool, args.lockfile)
    tool_data = _load_tool(args.lockfile, args.tool)
    version = tool_data.get("version")
    if version is None:
        raise SystemExit(
            f"Tool '{args.tool}' in '{args.lockfile}.lock.json' does not define a version",
        )
    print(version)
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
