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
"""Query tool metadata from the shared `tools/lockfiles/*.lock.json` catalog.

This script is intentionally small and dependency-free so shell-based
devcontainer feature installers and tests can ask two focused questions without
re-implementing JSON parsing or platform selection logic:

1. "What is the declared version for tool X?"
2. "Which binary metadata applies to tool X on this OS/CPU?"

The shell helper `tool_lockfile_helpers.sh` wraps this script for everyday use.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path


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


def _load_tool(lockfile: str, tool: str) -> dict:
    """Load one tool entry from a lockfile and fail with a clear message."""
    with _lockfile_path(lockfile).open(encoding="utf-8") as handle:
        data = json.load(handle)

    try:
        return data[tool]
    except KeyError as exc:
        raise SystemExit(
            f"Tool '{tool}' not found in lockfile '{lockfile}.lock.json'",
        ) from exc


def _select_binary(tool_data: dict, os_name: str, cpu: str) -> dict:
    """Pick the binary entry matching the requested platform."""
    for binary in tool_data["binaries"]:
        if binary["os"] == os_name and binary["cpu"] == cpu:
            return binary

    raise SystemExit(
        f"No binary defined for os={os_name!r}, cpu={cpu!r}",
    )


def _cmd_version(args: argparse.Namespace) -> int:
    """Print the declared version for one tool."""
    tool_data = _load_tool(args.lockfile, args.tool)
    version = tool_data.get("version")
    if version is None:
        raise SystemExit(
            f"Tool '{args.tool}' in '{args.lockfile}.lock.json' does not define a version",
        )
    print(version)
    return 0


def _cmd_env(args: argparse.Namespace) -> int:
    """Print selected binary metadata as `key=value` lines for shell callers."""
    tool_data = _load_tool(args.lockfile, args.tool)
    binary = _select_binary(tool_data, args.os, args.cpu)

    output = {}
    if "version" in tool_data:
        output["version"] = tool_data["version"]
    for key in ("kind", "url", "sha256", "file", "type", "os", "cpu"):
        if key in binary:
            output[key] = binary[key]

    for key, value in output.items():
        print(f"{key}={value}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Define a tiny CLI for version and platform-specific metadata lookups."""
    parser = argparse.ArgumentParser(
        description="Read tool metadata from multitool-compatible lockfiles.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    version_parser = subparsers.add_parser(
        "version",
        help="Print the version for a tool from a lockfile.",
    )
    version_parser.add_argument("--tool", required=True)
    version_parser.add_argument(
        "--lockfile",
        help="Lockfile basename without .lock.json, defaults to the tool name",
    )
    version_parser.set_defaults(func=_cmd_version)

    env_parser = subparsers.add_parser(
        "env",
        help="Print selected binary metadata as shell-style key=value lines.",
    )
    env_parser.add_argument("--tool", required=True)
    env_parser.add_argument(
        "--lockfile",
        help="Lockfile basename without .lock.json, defaults to the tool name",
    )
    env_parser.add_argument("--os", default=_detect_os())
    env_parser.add_argument("--cpu", default=_detect_cpu())
    env_parser.set_defaults(func=_cmd_env)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, fill in default lockfile names, and dispatch."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.lockfile is None:
        args.lockfile = args.tool
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
