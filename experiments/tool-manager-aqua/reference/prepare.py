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
"""Prepare a bounded release from native aqua and uv dependency-group owners.

Producer prerequisites: Python >=3.11, PyYAML, aqua, uv and Docker. Consumers of
outputs need neither this Python generator nor aqua. Known archive/name mappings
cover the migrated repository CLI layouts rather than arbitrary packages.
"""

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import tomllib

import yaml

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parents[2]
OWNER_DIR = BASE / "tools/owners/aqua"
sys.path.insert(0, str(BASE / "tools/internal/aqua"))
from export_native import native_lock  # noqa: E402

IMAGE = os.environ.get(
    "SCORE_PREPARED_RUNTIME_IMAGE", "score-tool-manager-comparison-base:20261031"
)


def run(*args, **kw):
    print("+", " ".join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, **kw)


def aqua_environment(source: Path) -> dict[str, str]:
    """Allow this worktree's pinned local registry without changing global policy."""
    environment = os.environ.copy()
    policy = str(source / "aqua-policy.yaml")
    existing = environment.get("AQUA_POLICY_CONFIG")
    if policy not in (existing or "").split(os.pathsep):
        environment["AQUA_POLICY_CONFIG"] = policy + (
            os.pathsep + existing if existing else ""
        )
    return environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--version", required=True, help="Facade release identifier")
    parser.add_argument(
        "--package-name",
        required=True,
        help="Configurable Python distribution identity for this local release.",
    )
    parser.add_argument(
        "--source", type=Path, default=OWNER_DIR, help="Isolated owner directory"
    )
    parser.add_argument(
        "--sync-repository",
        action="store_true",
        help="Regenerate actual root consumers and standard facade metadata",
    )
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine().lower() not in {
        "amd64",
        "x86_64",
    }:
        raise SystemExit(
            "Local reference release runtimes require a Linux amd64 producer; "
            "the production Dockerfile provisions its own target-platform tools"
        )
    out = args.output.resolve()
    if out.exists():
        raise SystemExit(
            "Use a fresh output directory; prepared releases are immutable"
        )
    out.mkdir(parents=True)
    aqua = Path(os.environ["AQUA_BINARY"]).resolve()
    uv = Path(os.environ["UV_BINARY"]).resolve()
    for file in (
        "aqua.yaml",
        "aqua-policy.yaml",
        "aqua-bootstrap.toml",
        "pyproject.toml",
        "starpls-registry.yaml",
        "apm-registry.yaml",
        "provision.sh",
    ):
        shutil.copy2(
            (ROOT if file == "provision.sh" else args.source) / file, out / file
        )
    config = out / "aqua.yaml"
    if (args.source / "aqua-checksums.json").exists():
        shutil.copy2(args.source / "aqua-checksums.json", out / "aqua-checksums.json")
    run(
        aqua,
        "-c",
        config,
        "update-checksum",
        "--prune",
        env=aqua_environment(out),
    )
    native = yaml.safe_load(config.read_text())["packages"]
    checksums = json.loads((out / "aqua-checksums.json").read_text())
    groups = tomllib.loads((out / "pyproject.toml").read_text())["dependency-groups"]

    def requirements(group):
        result = []
        for item in groups[group]:
            result.extend(
                requirements(item["include-group"])
                if isinstance(item, dict)
                else [item]
            )
        return result

    locks = native_lock(native, checksums)
    selections = {}
    bazel = out / "bazel"
    bazel.mkdir(parents=True)
    shutil.copy2(BASE / ".bazelversion", bazel / ".bazelversion")
    tools = bazel / "tools"
    (tools / "internal").mkdir(parents=True)
    (tools / "score_tools").mkdir()
    for rel in ("python_tool.bzl", "multitool.bzl", "internal/run_python_tool.sh"):
        shutil.copy2(BASE / "tools" / rel, tools / rel)
    # uv and uvx share the native aqua release owner.
    (tools / "uv.lock.json").write_text(
        json.dumps({k: locks[k] for k in ("uv", "uvx")}, indent=2) + "\n"
    )
    (tools / "native.lock.json").write_text(
        json.dumps({k: v for k, v in locks.items() if k not in {"uv", "uvx"}}, indent=2)
        + "\n"
    )
    for profile in groups:
        selected = [p for p in native if profile in p["tags"]]
        python = requirements(profile)
        selected_versions = {
            p["name"].rsplit("/", 1)[1].split("@")[0]: p["name"]
            .rsplit("@", 1)[1]
            .removeprefix("v")
            for p in selected
        }
        if "uv" in selected_versions:
            selected_versions["uvx"] = selected_versions["uv"]
        selected_versions.update(dict(r.split("==", 1) for r in python))
        selections[profile] = selected_versions
        (out / f"{profile}.requirements.txt").write_text("\n".join(python) + "\n")
        runtime = out / "runtime" / profile
        (runtime / "bin").mkdir(parents=True)
        run(
            aqua,
            "-c",
            config,
            "cp",
            "--tags",
            profile,
            "-o",
            runtime / "bin",
            env=aqua_environment(out),
        )
        if profile == "published" and any(
            package["name"].startswith("microsoft/apm@") and profile in package["tags"]
            for package in native
        ):
            environment = aqua_environment(out)
            run(aqua, "-c", config, "install", "--tags", profile, env=environment)
            apm_binary = run(
                aqua,
                "-c",
                config,
                "which",
                "apm",
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
            ).stdout.strip()
            runtime_tree = Path(apm_binary).resolve().parent
            if runtime_tree.name != "apm-linux-x86_64":
                raise SystemExit(
                    f"Unexpected prepared APM runtime path: {runtime_tree}"
                )
            apm_runtime = runtime / "lib/apm"
            apm_runtime.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(runtime_tree, apm_runtime, symlinks=True)
            (runtime / "bin/apm").unlink()
            (runtime / "bin/apm").symlink_to("../lib/apm/apm")
        # Fixed venv location is created inside the actual target Ubuntu ABI.
        container_name = os.environ.get("SCORE_PREPARE_CONTAINER_NAME")
        run(
            "docker",
            "run",
            "--rm",
            *(["--name", container_name] if container_name else []),
            "--user",
            "0:0",
            "--mount",
            f"type=bind,src={out},dst=/release",
            "--mount",
            f"type=bind,src={runtime},dst=/opt/score-tools",
            "--mount",
            f"type=bind,src={uv},dst=/bootstrap/uv,readonly",
            "--env",
            "UV_CACHE_DIR=/tmp/uv-cache",
            "--env",
            "NATIVE_PREPARED=1",
            "--env",
            "UV_BINARY=/bootstrap/uv",
            IMAGE,
            "bash",
            "/release/provision.sh",
            profile,
        )
    package = out / "package"
    package.mkdir()
    from sync_repository import outputs
    from prepare_dependency_release import prepare as prepare_dependency_release

    generated = outputs(out)
    if args.sync_repository:
        # Native hash refresh and all compatibility outputs belong to the same
        # explicit regeneration action. The source tool versions remain owners.
        shutil.copy2(out / "aqua-checksums.json", args.source / "aqua-checksums.json")
        for path, content in generated.items():
            path.write_text(content)
        run(sys.executable, BASE / "tools/internal/sync_readme.py")
    with tempfile.TemporaryDirectory(prefix=".dependency-release-", dir=out) as work:
        prepare_dependency_release(
            Path(work), args.version, args.package_name, out, str(uv)
        )
        package_metadata = Path(work) / "package/pyproject.toml"
        (package / "pyproject.toml").write_bytes(package_metadata.read_bytes())
        dist = out / "dist"
        dist.mkdir()
        release_wheel = next((Path(work) / "dist").glob("*.whl"))
        shutil.copy2(release_wheel, dist / release_wheel.name)
        shutil.copy2(Path(work) / "release.json", out / "release.json")
    python_catalog = {
        r.split("==")[0]: dict(
            package=r.split("==")[0],
            version=r.split("==")[1],
            entrypoint=r.split("==")[0],
        )
        for g in groups
        for r in requirements(g)
    }
    (tools / "score_tools/python_tools.bzl").write_text(
        "# Generated direct Python selections.\nPYTHON_TOOLS = "
        + repr(python_catalog)
        + "\n"
    )
    (tools / "BUILD.bazel").write_text(
        """# Native aliases preserve caller cwd via rules_multitool's :cwd launcher.
load(":multitool.bzl", "multitool_aliases")
load(":python_tool.bzl", "python_tool")
load(":score_tools/python_tools.bzl", "PYTHON_TOOLS")
package(default_visibility = ["//visibility:public"])
exports_files(["native.lock.json", "uv.lock.json"])
"""
        + "\n".join(f'multitool_aliases("{name}")' for name in list(locks))
        + "\n[python_tool(name) for name in PYTHON_TOOLS]\n"
    )
    (bazel / "MODULE.bazel").write_text("""module(name = "score_aqua_reference")
bazel_dep(name = "rules_multitool", version = "1.11.1")
bazel_dep(name = "rules_shell", version = "0.4.1")
# Native versions/artifact hashes, including uv/uvx, come from aqua owners.
multitool = use_extension("@rules_multitool//multitool:extension.bzl", "multitool")
multitool.hub(lockfile = "//tools:native.lock.json")
multitool.hub(lockfile = "//tools:uv.lock.json")
use_repo(multitool, "multitool")
""")
    (out / "selection.json").write_text(json.dumps(selections, indent=2) + "\n")
    (out / "README.md").write_text("""# Prepared aqua reference release

This directory snapshots authoritative aqua/Python-group definitions, generated
requirements, standard Python wheel/package metadata, portable Bazel module and
two complete prepared runtimes. Initial installation needs aqua, uv, compatible
system Python/Git and network: `AQUA_BINARY=/path/aqua UV_BINARY=/path/uv bash
provision.sh published /absolute/final/prefix` (or repository). Use a fresh prefix.
The installer and all inputs are here; no source checkout is needed.

Prepared runtimes were built at /opt/score-tools against Ubuntu Python3.12. Mount
the entire runtime/PROFILE read-only at /opt/score-tools; expose its bin directory.
Keep system Python/Git, writable home/tmp, and no producer manager on PATH. uv/uvx are deliberately delivered tools. Do not relocate
only venv/bin/pre-commit: its shebang and environment require that fixed prefix.
Both run-tool modes trust these installed versions inside the selected container.

The package wheel is consumed by native uv/uvx without aqua. The Bazel module
exposes //tools:ruff, //tools:shellcheck and //tools:pre-commit. Its pinned uvx helper
may initially fetch Python/Python packages; that route has no offline claim.
""")
    from images import prepare_context

    prepare_context(out)
    print(f"Prepared release: {out}")


if __name__ == "__main__":
    main()
