#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Bounded local A/B release gate; writes only fresh task destinations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_tools.provision import provision

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    records = []
    uv = shutil.which("uv")
    if not uv:
        raise SystemExit("uv required")

    def run(command, *, cwd=ROOT, expected=0, env=None):
        result = subprocess.run(
            list(map(str, command)), cwd=cwd, env=env, text=True, capture_output=True
        )
        records.append(
            {
                "argv": list(map(str, command)),
                "cwd": str(cwd),
                "exit": result.returncode,
                "stdout": result.stdout[-8000:],
                "stderr": result.stderr[-4000:],
            }
        )
        (output / "commands.json").write_text(json.dumps(records, indent=2) + "\n")
        if result.returncode != expected:
            raise RuntimeError(
                f"Expected exit {expected}, got {result.returncode}: {command}\n{result.stderr[-4000:]}"
            )
        return result

    snapshots = {}
    for label in ("a", "b"):
        snapshot = output / ("source-" + label)
        snapshot.mkdir()
        shutil.copytree(
            ROOT / "tools",
            snapshot / "tools",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        for filename in ("MODULE.bazel", "MODULE.bazel.lock", ".bazelversion"):
            shutil.copyfile(ROOT / filename, snapshot / filename)
        snapshots[label] = snapshot
    ruff_b = snapshots["b"] / "tools/lockfiles/ruff.lock.json"
    data = json.loads(ruff_b.read_text())
    old_version = data["ruff"]["version"]
    new_version = "0.14.6"
    if old_version == new_version:
        raise RuntimeError("The A/B fixture must select two different Ruff releases")
    data["ruff"]["version"] = new_version
    ruff_b.write_text(json.dumps(data, indent=2) + "\n")
    package_script = ROOT / "tools/internal/dependency_package.py"
    name = "score-own-release-local"
    releases = {}
    for label, version in (("a", "0.8.0"), ("b", "0.8.1")):
        root = snapshots[label] / "tools"
        release = output / ("release-" + label)
        if label == "b":
            stale = run(
                [
                    sys.executable,
                    package_script,
                    "check",
                    releases["a"],
                    "--catalog-root",
                    root,
                ],
                expected=1,
            )
            if "Stale native artifact" not in stale.stderr:
                raise RuntimeError(
                    "Changed native owner was not rejected before refresh"
                )
            spec = importlib.util.spec_from_file_location(
                "refresh", ROOT / "tools/internal/refresh_lockfile_digests.py"
            )
            refresh = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(refresh)
            changes = refresh.refresh_lockfile(ruff_b, token=None)
            (output / "refresh.json").write_text(json.dumps(changes, indent=2) + "\n")
        run(
            [
                sys.executable,
                package_script,
                "build",
                "--output",
                release,
                "--version",
                version,
                "--package-name",
                name,
                "--catalog-root",
                root,
                "--uv",
                uv,
            ]
        )
        run([sys.executable, package_script, "check", release, "--catalog-root", root])
        releases[label] = release
    run(
        [
            sys.executable,
            package_script,
            "check",
            releases["a"],
            "--catalog-root",
            snapshots["b"] / "tools",
        ],
        expected=1,
    )
    project = output / "consumer"
    project.mkdir()
    versions = {"a": old_version, "b": new_version}
    native = output / "native"
    sentinel_hash = None
    for label, version in (("a", "0.8.0"), ("b", "0.8.1")):
        (project / "pyproject.toml").write_text(
            '[project]\nname = "independent-consumer"\nversion = "1.0.0"\nrequires-python = ">=3.11"\n'
            f'dependencies = ["{name}[ruff]=={version}"]\n'
        )
        shutil.copyfile(project / "pyproject.toml", output / f"consumer-{label}.toml")
        wheel_dir = releases[label] / "dist"
        run([uv, "lock", "--find-links", wheel_dir], cwd=project)
        run([uv, "sync", "--find-links", wheel_dir], cwd=project)
        observed = run([uv, "run", "--no-sync", "ruff", "--version"], cwd=project)
        if observed.stdout.strip() != "ruff " + versions[label]:
            raise RuntimeError("uv did not select the owner Ruff version")
        observed = run(
            [
                uv,
                "tool",
                "run",
                "--find-links",
                wheel_dir,
                "--with",
                f"{name}[ruff]=={version}",
                "ruff",
                "--version",
            ],
            cwd=project,
        )
        if observed.stdout.strip() != "ruff " + versions[label]:
            raise RuntimeError("uvx did not select the generated Ruff pin")
        shutil.copyfile(project / "uv.lock", output / f"consumer-{label}.uv.lock")
        provision(
            "release",
            ["ruff", "buildifier"],
            [],
            bin_dir=native / "bin",
            data_dir=native / "data",
            root=snapshots[label] / "tools",
        )
        observed = run([native / "bin/ruff", "--version"])
        if observed.stdout.strip() != "ruff " + versions[label]:
            raise RuntimeError("Native prefix did not update")
        unrelated = {
            "target": os.readlink(native / "bin/buildifier"),
            "sha256": hashlib.sha256(
                (native / "bin/buildifier").read_bytes()
            ).hexdigest(),
        }
        if label == "a":
            sentinel_hash = unrelated
            (native / "bin/user-sentinel").write_text("unrelated-user-file\n")
        elif (
            unrelated != sentinel_hash
            or (native / "bin/user-sentinel").read_text() != "unrelated-user-file\n"
        ):
            raise RuntimeError("Native update changed unrelated tool/user sentinel")
        (output / f"native-{label}.json").write_text(
            json.dumps(
                {
                    "ruff": os.readlink(native / "bin/ruff"),
                    "buildifier": unrelated,
                    "user_sentinel": (native / "bin/user-sentinel").read_text(),
                },
                indent=2,
            )
            + "\n"
        )
    snapshot_b = snapshots["b"]
    fixture_dir = snapshot_b / "caller"
    fixture_dir.mkdir()
    (fixture_dir / "bad input.py").write_text("import os\n")
    bazel = shutil.which("bazel")
    if not bazel:
        raise RuntimeError("Bazel required for public-target gate")
    observed = run([bazel, "run", "//tools:ruff", "--", "--version"], cwd=fixture_dir)
    if observed.stdout.strip() != "ruff " + new_version:
        raise RuntimeError("Public Bazel Ruff target did not update")
    lint = run(
        [bazel, "run", "//tools:ruff", "--", "check", "bad input.py"],
        cwd=fixture_dir,
        expected=1,
    )
    if "F401" not in lint.stdout or "bad input.py" not in lint.stdout:
        raise RuntimeError(
            "Bazel failed to preserve caller cwd/argv/expected lint failure"
        )
    (output / "result.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "platform": "linux/x86_64",
                "ruff_a": old_version,
                "ruff_b": new_version,
                "releases": ["0.8.0", "0.8.1"],
                "name": name,
                "checks": [
                    "stale-owner-before-refresh",
                    "owner-bound-wheel-A-and-B",
                    "A-rejected-against-B",
                    "same-uv-project-release-only-update",
                    "ordinary-uvx-generated-pin",
                    "same-native-prefix-update-preserves-buildifier-and-user-sentinel",
                    "actual-public-Bazel-Ruff-version-and-relative-spaced-lint-exit-1",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    print(output / "result.json")


if __name__ == "__main__":
    main()
