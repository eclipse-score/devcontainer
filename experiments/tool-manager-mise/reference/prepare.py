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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Create an installable release, ordinary package metadata and simple Bazel module."""

import argparse
from pathlib import Path
import shlex
import shutil
import sys
from provision import command, provision

SOURCE = Path(__file__).resolve().parent
BASELINE = SOURCE.parents[2]
OWNER_ROOT = BASELINE / "tools" / "mise"


sys.path.insert(0, str(BASELINE))
from tools.internal.mise.refresh import (  # noqa: E402
    NATIVE,
    _configs,
    _python_catalog_text,
    export_native,
    root_outputs,
)
from tools.internal.mise.python_package import (  # noqa: E402
    _project_metadata,
    render_pyproject,
)


def prepare(destination, version, package_name, source=OWNER_ROOT):
    if destination.exists():
        raise ValueError("Use a fresh immutable release directory: " + str(destination))
    destination.mkdir(parents=True)
    for path in source.glob("mise.*"):
        shutil.copy2(path, destination / path.name)
    shutil.copy2(SOURCE / "provision.py", destination / "provision.py")
    shutil.copy2(
        BASELINE / "tools/internal/mise/bootstrap.sh", destination / "bootstrap.sh"
    )
    shutil.copy2(SOURCE / "install.sh", destination / "install.sh")
    # Keep ordinary native artifact locks separate from exact PyPI selections.
    command(
        destination,
        "repository",
        "lock",
        "--platform",
        "linux-x64,linux-arm64,macos-arm64",
        "aqua:rhysd/actionlint",
        "aqua:bazelbuild/bazelisk",
        "aqua:bazelbuild/buildtools/buildifier",
        "aqua:astral-sh/ruff",
        "aqua:koalaman/shellcheck",
        "aqua:google/yamlfmt",
        "uv",
        envs="native",
    )
    command(
        destination,
        "repository",
        "lock",
        "--platform",
        "linux-x64,linux-arm64,macos-arm64,macos-x64",
        "github:microsoft/apm",
        "aqua:anomalyco/opencode",
        envs="native",
    )
    command(
        destination,
        "repository",
        "lock",
        "--platform",
        "linux-x64,linux-arm64,macos-arm64",
        "github:withered-magic/starpls",
        envs="published",
    )
    tools = destination / "tools"
    (tools / "internal").mkdir(parents=True, exist_ok=True)
    (tools / "score_tools").mkdir(exist_ok=True)
    configs = _configs(destination)
    names = {backend: name for backend, name in NATIVE.items() if backend in configs}
    export_native(destination, configs, names)
    for filename in ("python_tool.bzl", "multitool.bzl", "internal/run_python_tool.sh"):
        shutil.copy2(BASELINE / "tools" / filename, tools / filename)
    # Preserve catalog metadata and public entrypoints; derive all direct pins.
    (tools / "score_tools/python_tools.bzl").write_text(_python_catalog_text(configs))
    sys.path.insert(0, str(BASELINE / "tools"))
    from score_tools.catalog import _parse_python_tool_catalog

    catalog = _parse_python_tool_catalog()
    (tools / "BUILD.bazel").write_text(
        """# Generated registrations expose the fixed reference selection.
load(":multitool.bzl", "multitool_aliases")
load(":python_tool.bzl", "python_tool")
package(default_visibility = ["//visibility:public"])
exports_files(glob(["*.lock.json", "score_tools/*.bzl"]))
"""
        + "".join(f'multitool_aliases("{name}")\n' for name in names.values())
        + """multitool_aliases("uvx")
"""
        + "".join(f'python_tool("{name}")\n' for name in catalog)
    )
    (destination / "MODULE.bazel").write_text(
        """# Generated: portable binary hubs use the existing Multitool runtime.
module(name = "score_mise_reference")
bazel_dep(name = "rules_multitool", version = "1.11.1")
bazel_dep(name = "rules_shell", version = "0.4.1")
multitool = use_extension("@rules_multitool//multitool:extension.bzl", "multitool")
"""
        + "".join(
            f'multitool.hub(lockfile = "//tools:{name}.lock.json")\n'
            for name in names.values()
        )
        + """multitool.hub(lockfile = "//tools:uv.lock.json")
use_repo(multitool, "multitool")
register_toolchains("@multitool//toolchains:all")
"""
    )
    (destination / "README.md").write_text("""# Prepared mise reference release

This local release contains native metadata, complete selected runtime trees,
an ordinary Python facade, and the existing Bazel compatibility outputs.
`mise.native.toml`, `mise.python.toml`, and `mise.published.toml` preserve the
owner selections. `install.sh` is a release-layout fixture; production feature
and repository setup provision their selected tools directly from `tools/mise`.
The Python package has ordinary extras and requires no mise at install or run
time. Bazel retains the existing native labels and uvx launcher.
""")
    (destination / ".bazelversion").write_text((BASELINE / ".bazelversion").read_text())
    package_metadata = _project_metadata(version, package_name, source)
    (destination / "pyproject.toml").write_text(render_pyproject(package_metadata))
    copied = set()
    for profile in ("published", "repository"):
        selected = provision(destination, profile)
        profiles = destination / "profiles"
        profiles.mkdir(exist_ok=True)
        for tool in selected.values():
            prefix = tool["root"]
            if prefix not in copied:
                shutil.copytree(
                    prefix,
                    destination / "native" / prefix.lstrip("/"),
                    symlinks=True,
                    dirs_exist_ok=True,
                )
                copied.add(prefix)
        # Shell metadata is generated from the resolved native selection, so
        # image assembly needs no Python or manager merely to select commands.
        data = {
            "prefixes": [tool["root"] for tool in selected.values()],
            "commands": list(selected),
            "executables": [
                tool["bin"] + "/" + name for name, tool in selected.items()
            ],
        }
        (profiles / (profile + ".sh")).write_text(
            "# Generated from native mise profile resolution.\n"
            + "".join(
                name + "=(" + " ".join(shlex.quote(item) for item in values) + ")\n"
                for name, values in data.items()
            )
        )
    print(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path, nargs="?")
    parser.add_argument("--version", required=True)
    parser.add_argument("--package-name", required=True)
    parser.add_argument("--source", type=Path, default=OWNER_ROOT)
    parser.add_argument("--root", choices=("write", "check"))
    args = parser.parse_args()
    source = args.source.resolve()
    if args.destination is None:
        parser.error("destination is required")
    if not args.destination.exists():
        prepare(
            args.destination.resolve(),
            args.version,
            args.package_name,
            source=source,
        )
    elif not args.root:
        parser.error(
            "Use a fresh release directory, or --root to apply/check existing release"
        )
    if args.root:
        root_outputs(
            args.destination.resolve(),
            check=args.root == "check",
            source=source,
        )
