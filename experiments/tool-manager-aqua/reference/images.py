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
"""Assemble real COPY-based local images from a prepared release."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tomllib

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def prepare_context(release):
    for file in ("Dockerfile", "image-check.py"):
        shutil.copy2(HERE / file, release / file)
    shutil.copy2(REPO / "tools/run-tool", release / "run-tool")
    shutil.copy2(REPO / ".bazelversion", release / ".bazelversion")
    selections = json.loads((release / "selection.json").read_text())
    for profile, versions in selections.items():
        (release / f"{profile}.expected.json").write_text(
            json.dumps(
                dict(
                    profile=profile,
                    versions=versions,
                    bazel_version=(REPO / ".bazelversion").read_text().strip(),
                ),
                indent=2,
            )
            + "\n"
        )


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("release", type=Path)
    p.add_argument("--build", action="store_true")
    args = p.parse_args()
    release = args.release.resolve()
    prepare_context(release)
    if args.build:
        version = tomllib.loads((release / "package/pyproject.toml").read_text())[
            "project"
        ]["version"]
        for profile in json.loads((release / "selection.json").read_text()):
            subprocess.run(
                [
                    "docker",
                    "build",
                    "-t",
                    f"score-aqua-m2:{version}-{profile}",
                    "--build-arg",
                    f"PROFILE={profile}",
                    "--build-arg",
                    "BAZEL_VERSION=" + (REPO / ".bazelversion").read_text().strip(),
                    str(release),
                ],
                check=True,
            )


if __name__ == "__main__":
    main()
