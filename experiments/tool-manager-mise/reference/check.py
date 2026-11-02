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
"""Verify a prepared release through real root consumers and copied images."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tomllib
from prepare import BASELINE, OWNER_ROOT, SOURCE, root_outputs


class Check:
    def __init__(self, release, evidence):
        self.release = release
        self.evidence = evidence
        evidence.mkdir(parents=True, exist_ok=True)
        self.records = []
        self.state = Path("/tmp/score-mise-m2-check-state")
        self.state.mkdir(exist_ok=True)
        self.env = dict(
            os.environ,
            PATH="/usr/bin:/bin",
            UV_PYTHON="/usr/bin/python3",
            UV_PYTHON_DOWNLOADS="never",
            UV_CACHE_DIR=str(self.state / "uv-cache"),
        )
        self.selected = {
            p: json.loads((release / (p + ".runtime.json")).read_text())
            for p in ("repository", "published")
        }

    def run(self, args, cwd=BASELINE, expect=0, env=None):
        result = subprocess.run(
            [str(a) for a in args],
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.records.append(
            dict(
                argv=[str(a) for a in args],
                cwd=str(cwd),
                status=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        )
        (self.evidence / "commands.json").write_text(
            json.dumps(self.records, indent=2) + "\n"
        )
        assert result.returncode == expect, self.records[-1]
        return result.stdout + result.stderr

    def root(self):
        env = dict(
            os.environ,
            UV_PYTHON_PREFERENCE="only-managed",
            UV_PYTHON_DOWNLOADS="automatic",
            UV_PYTHON_INSTALL_DIR=str(self.state / "bazel-python"),
            UV_CACHE_DIR=str(self.state / "bazel-uv-cache"),
            BAZELISK_HOME=str(self.state / "bazelisk"),
        )
        bazel = [shutil.which("bazel"), "--output_base=/tmp/score-mise-m2-root-bazel"]
        flags = {
            "actionlint": ["-version"],
            "buildifier": ["-version"],
            "yamlfmt": ["-version"],
            "bazelisk": [
                "--output_user_root=/tmp/score-mise-m2-nested-bazel",
                "version",
            ],
        }
        for name, selected in self.selected["repository"].items():
            output = self.run(
                [
                    *bazel,
                    "run",
                    "//tools:" + name,
                    "--",
                    *flags.get(name, ["--version"]),
                ],
                env=env,
            )
            assert re.search(
                r"(?<![\d.])" + re.escape(selected["version"]) + r"(?![\d.])", output
            ), (name, output)
        self.run([*bazel, "mod", "deps", "--lockfile_mode=error"], env=env)
        self.run([*bazel, "mod", "tidy"], env=env)

    def hooks(self):
        selected = self.selected["repository"]
        bins = list(dict.fromkeys(v["bin"] for v in selected.values()))
        env = dict(
            os.environ,
            PATH=":".join(bins + [os.environ["PATH"]]),
            PRE_COMMIT_HOME=str(self.state / "precommit"),
        )
        precommit = Path(selected["pre-commit"]["bin"]) / "pre-commit"
        for hook, file in [
            ("ruff-format", "tools/score_tools/catalog.py"),
            ("ruff-check", "tools/score_tools/catalog.py"),
            ("shellcheck", "tools/run-tool"),
            ("yamlfmt", ".pre-commit-config.yaml"),
            ("buildifier", "tools/BUILD.bazel"),
            ("actionlint", ".github/workflows/ci.yaml"),
        ]:
            self.run([precommit, "run", hook, "--files", file], env=env)

    def uv(self):
        uv = shutil.which("uv")
        uvx = shutil.which("uvx")
        self.run(
            [uv, "build", "--wheel", "--out-dir", self.release / "dist", self.release],
            env=self.env,
        )
        wheel = next((self.release / "dist").glob("*.whl"))
        for profile, selected in self.selected.items():
            consumer = self.evidence / ("consumer-" + profile)
            consumer.mkdir(exist_ok=True)
            extras = [
                n
                for n in ("ruff", "pre-commit", "pytest", "basedpyright")
                if n in selected
            ]
            spec = "score-mise-reference[" + ",".join(extras) + "] @ " + wheel.as_uri()
            (consumer / "pyproject.toml").write_text(
                '[project]\nname="real-consumer"\nversion="0.0.0"\nrequires-python=">=3.12"\n'
            )
            self.run([uv, "add", "--raw", spec], consumer, env=self.env)
            lock = tomllib.loads((consumer / "uv.lock").read_text())
            versions = {p["name"]: p["version"] for p in lock["package"]}
            metadata = json.loads(
                self.run(
                    [
                        uv,
                        "run",
                        "--locked",
                        "python",
                        "-c",
                        'import importlib.metadata as m,json; print(json.dumps(m.metadata("score-mise-reference").get_all("Requires-Dist")))',
                    ],
                    consumer,
                    env=self.env,
                )
            )
            (consumer / "Requires-Dist.json").write_text(
                json.dumps(metadata, indent=2) + "\n"
            )
            for name in extras:
                expected = selected[name]["version"]
                assert versions[name] == expected
                assert any(r.startswith(name + "==" + expected + ";") for r in metadata)
                for command in (
                    [uv, "run", "--locked", name, "--version"],
                    [uvx, "--with", spec, name, "--version"],
                ):
                    output = self.run(command, consumer, env=self.env)
                    assert expected in output, (name, output)
            if profile == "published":
                (consumer / "test_selected.py").write_text(
                    "def test_selected():\n    assert 6 * 7 == 42\n"
                )
                self.run(
                    [uv, "run", "--locked", "pytest", "-q", "test_selected.py"],
                    consumer,
                    env=self.env,
                )
                (consumer / "type_error.py").write_text('value: int = "wrong"\n')
                assert "reportAssignmentType" in self.run(
                    [uv, "run", "--locked", "basedpyright", "type_error.py"],
                    consumer,
                    expect=1,
                    env=self.env,
                )

    def images(self, build):
        for profile, selected in self.selected.items():
            image = "score-mise-" + profile + "-m2:" + self.release.name
            if build:
                shutil.copy2(SOURCE / "Dockerfile", self.release / "Dockerfile")
                self.run(
                    [
                        "docker",
                        "build",
                        "--build-arg",
                        "PROFILE=" + profile,
                        "-t",
                        image,
                        self.release,
                    ]
                )
            expected = self.evidence / (profile + ".expected.json")
            expected.write_text(
                json.dumps(
                    dict(
                        profile=profile,
                        versions={
                            n: v["version"]
                            for n, v in selected.items()
                            if not n.endswith("-langserver")
                        },
                        bazel_version=(BASELINE / ".bazelversion").read_text().strip(),
                    ),
                    indent=2,
                )
                + "\n"
            )
            output = self.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network=none",
                    "--user=12345:12345",
                    "--mount",
                    f"type=bind,src={SOURCE / 'repository-runtime-check.py'},dst=/check.py,readonly",
                    "--mount",
                    f"type=bind,src={expected},dst=/expected.json,readonly",
                    "--mount",
                    f"type=bind,src={BASELINE / 'tools/run-tool'},dst=/run-tool,readonly",
                    image,
                    "python3",
                    "/check.py",
                    "/expected.json",
                    "/run-tool",
                ]
            )
            (self.evidence / (profile + ".runtime.jsonl")).write_text(output)
            self.run(["docker", "image", "inspect", image])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("release", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument(
        "--phase", choices=["all", "root", "hooks", "uv", "images"], default="all"
    )
    parser.add_argument("--build-images", action="store_true")
    parser.add_argument("--source", type=Path, default=OWNER_ROOT)
    args = parser.parse_args()
    if args.phase in ("all", "root"):
        root_outputs(args.release.resolve(), check=True, source=args.source.resolve())
    check = Check(args.release.resolve(), args.evidence.resolve())
    for phase in ("root", "hooks", "uv", "images"):
        if args.phase in ("all", phase):
            getattr(check, phase)(args.build_images) if phase == "images" else getattr(
                check, phase
            )()
    print("PASS", args.phase, args.evidence)
