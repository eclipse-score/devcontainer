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
"""Refresh mise owner locks and export the compatibility metadata."""

import argparse
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
TOOLS_ROOT = REPOSITORY_ROOT / "tools"
OWNER_ROOT = TOOLS_ROOT / "mise"
SCHEMA = "https://raw.githubusercontent.com/bazel-contrib/rules_multitool/main/lockfile.schema.json"

# Native version strings come from the owner files. This map only names the
# existing public Bazel lock metadata that each selected runtime supplies.
NATIVE = {
    "aqua:rhysd/actionlint": "actionlint",
    "aqua:bazelbuild/bazelisk": "bazelisk",
    "aqua:bazelbuild/buildtools/buildifier": "buildifier",
    "aqua:astral-sh/ruff": "ruff",
    "aqua:koalaman/shellcheck": "shellcheck",
    "aqua:google/yamlfmt": "yamlfmt",
    "github:microsoft/apm": "apm",
    "aqua:anomalyco/opencode": "opencode",
    "github:withered-magic/starpls": "starpls",
    "uv": "uv",
}


def _configs(owner_root):
    configs = {}
    for name in ("native", "published", "python"):
        with (owner_root / f"mise.{name}.toml").open("rb") as handle:
            configs.update(tomllib.load(handle)["tools"])
    return configs


def export_native(release, config, names, output_root=None):
    """Export portable Bazel locks from the exact mise artifact locks."""
    locks = {}
    for path in release.glob("mise.*.lock"):
        locks.update(tomllib.loads(path.read_text())["tools"])
    output_root = output_root or release / "tools"
    output_root.mkdir(parents=True, exist_ok=True)
    for backend, name in names.items():
        selected = locks[backend][0]
        if selected["version"] != config[backend]:
            raise SystemExit(
                f"Stale mise artifact lock for {backend}: "
                f"owner={config[backend]}, lock={selected['version']}; "
                "run tools/internal/mise/refresh.sh"
            )
        outputs = [name, "uvx"] if name == "uv" else [name]
        definitions = {"$schema": SCHEMA}
        for executable in outputs:
            # Descriptions and public tool names remain in the compatibility
            # catalog; this exporter owns only their selected version/assets.
            metadata = json.loads(
                (REPOSITORY_ROOT / "tools/lockfiles" / f"{name}.lock.json").read_text()
            )[executable]
            artifacts = []
            for platform_name, artifact in selected.items():
                if not platform_name.startswith("platforms."):
                    continue
                system, cpu = platform_name.removeprefix("platforms.").split("-", 1)
                kind, digest = artifact["checksum"].split(":", 1)
                assert kind == "sha256"
                entry = dict(
                    kind="file",
                    url=artifact["url"],
                    sha256=digest,
                    os=system,
                    cpu={"x64": "x86_64", "arm64": "arm64"}[cpu],
                )
                archive = artifact["url"].rsplit("/", 1)[-1]
                extension = next(
                    (
                        suffix
                        for suffix in (".tar.gz", ".tar.xz", ".zip")
                        if archive.endswith(suffix)
                    ),
                    None,
                )
                if extension is not None:
                    archive_type = extension.removeprefix(".")
                    if name in ("ruff", "uv"):
                        member = archive.removesuffix(extension) + "/" + executable
                    elif name == "shellcheck":
                        member = "shellcheck-v" + selected["version"] + "/shellcheck"
                    elif name == "apm":
                        directory = archive.removesuffix(extension)
                        member = directory + "/" + executable
                        entry["dir"] = directory
                    else:
                        member = executable
                    entry.update(kind="archive", file=member, type=archive_type)
                artifacts.append(entry)
            existing = {(item["os"], item["cpu"]) for item in metadata["binaries"]}
            exported = {(item["os"], item["cpu"]) for item in artifacts}
            assert exported == existing, (
                name,
                sorted(existing - exported),
                sorted(exported - existing),
            )
            metadata.update(version=config[backend], binaries=artifacts)
            definitions[executable] = metadata
        (output_root / f"{name}.lock.json").write_text(
            json.dumps(definitions, indent=2) + "\n"
        )


def _python_catalog_text(configs):
    sys.path.insert(0, str(TOOLS_ROOT))
    from score_tools.catalog import _parse_python_tool_catalog

    catalog = _parse_python_tool_catalog()
    for metadata in catalog.values():
        metadata["version"] = configs["pypi:" + metadata["package"]]
    header = (
        Path(__file__)
        .read_text()
        .split('"""', 1)[0]
        .removeprefix("#!/usr/bin/env python3\n")
    )
    literal = json.dumps(catalog, indent=4)
    formatted = []
    for line in literal.splitlines():
        stripped = line.strip()
        indentation = len(line) - len(line.lstrip())
        if stripped == "}" and indentation:
            line += ","
        elif ":" in stripped and not stripped.endswith(("{", ",")):
            line += ","
        formatted.append(line)
    return (
        header
        + "# Generated by tools/internal/mise/refresh.py; metadata is maintained here, versions in tools/mise/mise.python.toml.\nPYTHON_TOOLS = "
        + "\n".join(formatted)
        + "\n"
    )


def root_outputs(release, check=False, source=OWNER_ROOT):
    """Apply/check generated native and Python compatibility consumers."""
    for name in (
        "mise.native.toml",
        "mise.python.toml",
        "mise.published.toml",
        "mise.native.lock",
        "mise.published.lock",
    ):
        if (release / name).read_bytes() != (source / name).read_bytes():
            raise SystemExit(
                "Stale release input: " + name + "; refresh current mise owners first"
            )
    sources = {}
    for path in (release / "tools").glob("*.lock.json"):
        definitions = {"$schema": SCHEMA, **json.loads(path.read_text())}
        sources[TOOLS_ROOT / "lockfiles" / path.name] = (
            json.dumps(definitions, indent=2) + "\n"
        )
    sources[TOOLS_ROOT / "score_tools/python_tools.bzl"] = (
        release / "tools/score_tools/python_tools.bzl"
    ).read_text()
    stale = [
        str(path.relative_to(REPOSITORY_ROOT))
        for path, data in sources.items()
        if not path.exists() or path.read_text() != data
    ]
    if check:
        if stale:
            raise SystemExit("Generated drift: " + ", ".join(stale))
    else:
        for path, data in sources.items():
            path.write_text(data)
    return stale


def refresh_owner_locks(owner_root=OWNER_ROOT):
    """Resolve exact native asset pins for all declared supported platforms."""
    binary = os.environ.get("MISE_BINARY")
    if not binary:
        raise SystemExit("Set MISE_BINARY to the checksum-pinned mise bootstrap")
    machine = platform.machine().lower()
    if platform.system() != "Linux" or machine not in {"x86_64", "amd64"}:
        raise SystemExit("Owner refresh currently requires a Linux x86_64 host")
    with tempfile.TemporaryDirectory(prefix="score-mise-refresh-") as temporary:
        state = Path(temporary)
        env = os.environ.copy()
        env.update(
            MISE_CACHE_DIR=str(state / "cache"),
            MISE_CONFIG_DIR=str(state / "config"),
            MISE_DATA_DIR=str(state / "data"),
            MISE_STATE_DIR=str(state / "state"),
            MISE_SYSTEM_CONFIG_DIR=str(state / "system-config"),
            MISE_TRUSTED_CONFIG_PATHS=str(owner_root),
            MISE_YES="1",
        )
        common = [
            "aqua:rhysd/actionlint",
            "aqua:bazelbuild/bazelisk",
            "aqua:bazelbuild/buildtools/buildifier",
            "aqua:astral-sh/ruff",
            "aqua:koalaman/shellcheck",
            "aqua:google/yamlfmt",
            "uv",
        ]
        calls = (
            ("native", "linux-x64,linux-arm64,macos-arm64", common),
            (
                "native",
                "linux-x64,linux-arm64,macos-arm64,macos-x64",
                ["github:microsoft/apm", "aqua:anomalyco/opencode"],
            ),
            (
                "published",
                "linux-x64,linux-arm64,macos-arm64",
                ["github:withered-magic/starpls"],
            ),
        )
        for profile, platforms, backends in calls:
            subprocess.run(
                [
                    binary,
                    "-C",
                    str(owner_root),
                    "-E",
                    profile,
                    "lock",
                    "--platform",
                    platforms,
                    *backends,
                ],
                check=True,
                env=env,
            )


def refresh_root_outputs(check=False, source=OWNER_ROOT):
    """Export current owner locks without installing tools or making a release."""
    with tempfile.TemporaryDirectory(prefix="score-mise-export-") as temporary:
        release = Path(temporary)
        for path in source.glob("mise.*"):
            shutil.copy2(path, release / path.name)
        tools = release / "tools"
        (tools / "score_tools").mkdir(parents=True)
        configs = _configs(source)
        names = {
            backend: name for backend, name in NATIVE.items() if backend in configs
        }
        export_native(release, configs, names)
        (tools / "score_tools/python_tools.bzl").write_text(
            _python_catalog_text(configs)
        )
        return root_outputs(release, check=check, source=source)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.refresh == args.check:
        parser.error("choose exactly one of --refresh or --check")
    if args.refresh:
        refresh_owner_locks()
        refresh_root_outputs()
        return
    refresh_root_outputs(check=True)
    print("Owner locks and compatibility outputs are current")


if __name__ == "__main__":
    main()
