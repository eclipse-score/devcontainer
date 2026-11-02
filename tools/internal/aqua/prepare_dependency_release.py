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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Build a local standard dependency wheel from the current tool owners."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from python_package import package_metadata, release_manifest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OWNER_DIR = REPO / "tools/owners/aqua"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(output: Path, version: str, package_name: str, owner_dir: Path, uv: str):
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Release output must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    package_dir = output / "package"
    package_dir.mkdir()
    (package_dir / "pyproject.toml").write_text(
        package_metadata(owner_dir, version, package_name), encoding="utf-8"
    )
    dist = output / "dist"
    dist.mkdir()
    command = [
        uv,
        "--no-config",
        "build",
        "--wheel",
        "--python",
        sys.executable,
        "--out-dir",
        str(dist),
        str(package_dir),
    ]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True, env=os.environ.copy())
    wheels = sorted(dist.glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"Expected one dependency wheel in {dist}, found {wheels}")
    manifest = release_manifest(
        owner_dir,
        version,
        package_name,
        wheels[0].name,
        sha256(wheels[0]),
    )
    (output / "selection.json").write_text(
        json.dumps(manifest["selection"], indent=2) + "\n", encoding="utf-8"
    )
    (output / "release.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--package-name",
        required=True,
        help="Configurable Python distribution identity for this local release.",
    )
    parser.add_argument("--owner-dir", type=Path, default=OWNER_DIR)
    parser.add_argument(
        "--uv", default=os.environ.get("UV_BINARY") or shutil.which("uv")
    )
    args = parser.parse_args()
    if args.uv is None:
        parser.error("uv is required (set UV_BINARY or pass --uv)")
    prepare(args.output, args.version, args.package_name, args.owner_dir, args.uv)


if __name__ == "__main__":
    main()
