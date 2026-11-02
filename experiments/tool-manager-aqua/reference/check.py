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
"""Check the real root consumers and COPY-based images of a prepared M2 release."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tomllib
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OWNER_DIR = REPO / "tools/owners/aqua"
SYNC_REPOSITORY = REPO / "tools/internal/aqua/sync_repository.py"
STATE = Path("/tmp/score-aqua-reference/m2")


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("release", type=Path)
    p.add_argument("evidence", type=Path)
    p.add_argument(
        "--hooks",
        action="store_true",
        help="Exercise real local hook IDs on representative repository files",
    )
    args = p.parse_args()
    release = args.release.resolve()
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    selected = json.loads((release / "selection.json").read_text())
    version = tomllib.loads((release / "package/pyproject.toml").read_text())[
        "project"
    ]["version"]
    # An old release cannot validate new native owner decisions merely because
    # checked-in generated outputs happen to equal that old release's metadata.
    for file, loader in [
        ("aqua.yaml", yaml.safe_load),
        ("aqua-policy.yaml", yaml.safe_load),
        ("starpls-registry.yaml", yaml.safe_load),
        ("apm-registry.yaml", yaml.safe_load),
        ("pyproject.toml", tomllib.loads),
    ]:
        assert (release / file).is_file(), "Stale release owner snapshot: " + file
        assert loader((release / file).read_text()) == loader(
            (OWNER_DIR / file).read_text()
        ), "Stale release owner snapshot: " + file
    env = dict(
        os.environ,
        UV_CACHE_DIR=str(STATE / "uv-cache"),
        UV_PYTHON_INSTALL_DIR=str(STATE / "python"),
        UV_PYTHON_DOWNLOADS="automatic",
        BAZELISK_HOME=str(STATE / "bazelisk-cache"),
        PRE_COMMIT_HOME=str(STATE / "pre-commit"),
    )
    commands = []

    def run(argv, cwd=REPO, expected=0, override=None):
        print("+", " ".join(map(str, argv)), flush=True)
        result = subprocess.run(
            list(map(str, argv)),
            cwd=cwd,
            env=override or env,
            capture_output=True,
            text=True,
        )
        commands.append(
            dict(
                argv=list(map(str, argv)),
                cwd=str(cwd),
                exit=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
        (evidence / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        if result.returncode != expected:
            raise RuntimeError(commands[-1])
        return result.stdout + result.stderr

    run(
        [
            "/usr/bin/python3",
            SYNC_REPOSITORY,
            "--check",
        ]
    )
    run(["/usr/bin/python3", REPO / "tools/internal/sync_readme.py", "--check"])
    # These targets are the existing checkout's MODULE/BUILD consumers. The
    # former isolated reference module is deliberately not used for M2 proofs.
    flags = {
        "actionlint": ["-version"],
        "buildifier": ["-version"],
        "yamlfmt": ["-version"],
        "bazelisk": ["--output_base=" + str(STATE / "nested-bazel"), "version"],
    }
    bazel = [
        "bazel",
        "--output_base=" + str(STATE / "root-bazel"),
        "run",
        "--lockfile_mode=update",
    ]
    for name, expected in selected["repository"].items():
        observed = run(
            [*bazel, "//tools:" + name, "--", *flags.get(name, ["--version"])]
        )
        assert re.search(
            r"(?<![\d.])" + re.escape(expected) + r"(?![\d.])", observed
        ), (name, observed)
    for profile in selected:
        image = f"score-aqua-m2:{version}-{profile}"
        run(["docker", "image", "inspect", image, "--format", "{{.Id}}"])
        run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--tmpfs",
                "/tmp:mode=1777",
                image,
            ]
        )
    uv = str(Path(env.get("UV_BINARY") or shutil.which("uv") or "uv").resolve())
    uvx = str(
        Path(
            env.get("UVX_BINARY") or shutil.which("uvx") or Path(uv).with_name("uvx")
        ).resolve()
    )
    run(
        [
            "/usr/bin/python3",
            REPO / "tools/internal/aqua/check_dependency_release.py",
            release,
            evidence / "dependency-package",
            "--uv",
            uv,
            "--uvx",
            uvx,
        ],
        override=env,
    )
    if args.hooks:
        home = STATE / "hook-home"
        home.mkdir(exist_ok=True)
        gitdir = subprocess.check_output(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=REPO,
            text=True,
        ).strip()
        docker = [
            "docker",
            "run",
            "--rm",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--mount",
            f"type=bind,src={REPO},dst={REPO}",
            "--mount",
            f"type=bind,src={gitdir},dst={gitdir},readonly",
            "--mount",
            f"type=bind,src={home},dst=/hook-home",
            "--env",
            "HOME=/hook-home",
            "--env",
            "PRE_COMMIT_HOME=/hook-home/pre-commit",
            "--workdir",
            str(REPO),
            f"score-aqua-m2:{version}-repository",
        ]
        representatives = {
            "ruff-format": "tools/score_tools/catalog.py",
            "ruff-check": "tools/score_tools/catalog.py",
            "shellcheck": "tools/run-tool",
            "yamlfmt": ".github/workflows/ci.yaml",
            "buildifier": "tools/BUILD.bazel",
            "actionlint": ".github/workflows/ci.yaml",
        }
        for hook, file in representatives.items():
            run([*docker, "pre-commit", "run", hook, "--files", file])
    (evidence / "summary.json").write_text(
        json.dumps(
            dict(
                result="passed",
                release=str(release),
                selected=selected,
                hooks=args.hooks,
                commands=len(commands),
            ),
            indent=2,
        )
        + "\n"
    )
    print("M2 repository consumers passed:", evidence)


if __name__ == "__main__":
    main()
