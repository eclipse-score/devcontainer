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
"""Exercise a local dependency wheel through standard uv and uvx consumers."""

from __future__ import annotations

import argparse
from email import message_from_bytes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from python_package import owner_digest, selected_versions


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OWNER_DIR = REPO / "tools/owners/aqua"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def check(release: Path, evidence: Path, owner_dir: Path, uv: str, uvx: str) -> None:
    release = release.resolve()
    evidence = evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    report_path = evidence / "commands.json"
    consumer = evidence / "consumer"
    if consumer.exists():
        raise SystemExit(f"Consumer directory must be fresh: {consumer}")

    manifest = json.loads((release / "release.json").read_text(encoding="utf-8"))
    wheel = release / "dist" / manifest["wheel"]["filename"]
    if not wheel.is_file() or sha256(wheel) != manifest["wheel"]["sha256"]:
        raise SystemExit("Release wheel does not match release.json")
    with zipfile.ZipFile(wheel) as archive:
        metadata_files = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_files) != 1:
            raise SystemExit(
                f"Expected one wheel METADATA file, found {metadata_files}"
            )
        metadata = message_from_bytes(archive.read(metadata_files[0]))
    if normalized_name(metadata.get("Name", "")) != normalized_name(
        manifest["package"]
    ):
        raise SystemExit("Wheel distribution identity does not match release.json")
    if metadata.get("Version") != manifest["version"]:
        raise SystemExit("Wheel version does not match release.json")
    if manifest["owner_digest"] != owner_digest(owner_dir):
        raise SystemExit("Release owner digest is stale")
    if manifest["selection"] != selected_versions(owner_dir):
        raise SystemExit("Release tool selection does not match current owners")

    env = dict(os.environ)
    env["PATH"] = "/usr/bin:/bin"
    env["PYTHONNOUSERSITE"] = "1"
    commands: list[dict] = []

    def run(argv: list[str], cwd: Path | None = None) -> str:
        print("+", " ".join(argv), flush=True)
        result = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
        )
        commands.append(
            {
                "argv": argv,
                "cwd": str(cwd) if cwd else None,
                "exit": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        report_path.write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
        if result.returncode:
            raise RuntimeError(commands[-1])
        return result.stdout + result.stderr

    run(
        [
            uv,
            "--no-config",
            "init",
            "--bare",
            "--no-workspace",
            "--python",
            sys.executable,
            str(consumer),
        ]
    )
    requirement = f"{manifest['package']}[repository] @ {wheel.as_uri()}"
    run([uv, "--no-config", "add", "--raw", requirement], cwd=consumer)
    run([uv, "--no-config", "lock"], cwd=consumer)
    run([uv, "--no-config", "sync", "--locked"], cwd=consumer)

    expected = manifest["selection"]["repository"]["ruff"]
    observed = run(
        [uv, "--no-config", "run", "--locked", "ruff", "--version"], cwd=consumer
    )
    if f"ruff {expected}" not in observed:
        raise AssertionError(f"uv run selected an unexpected Ruff version: {observed}")
    observed = run(
        [uvx, "--no-config", "--with", requirement, "ruff", "--version"],
        cwd=consumer,
    )
    if f"ruff {expected}" not in observed:
        raise AssertionError(f"uvx selected an unexpected Ruff version: {observed}")

    summary = {
        "result": "passed",
        "package": manifest["package"],
        "version": manifest["version"],
        "wheel": str(wheel),
        "ruff": expected,
        "commands": len(commands),
        "consumer": str(consumer),
    }
    (evidence / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--owner-dir", type=Path, default=OWNER_DIR)
    parser.add_argument(
        "--uv", default=os.environ.get("UV_BINARY") or shutil.which("uv")
    )
    parser.add_argument(
        "--uvx", default=os.environ.get("UVX_BINARY") or shutil.which("uvx")
    )
    args = parser.parse_args()
    if args.uv is None or args.uvx is None:
        parser.error(
            "uv and uvx are required (set UV_BINARY and UVX_BINARY or pass both)"
        )
    check(args.release, args.evidence, args.owner_dir, args.uv, args.uvx)


if __name__ == "__main__":
    main()
