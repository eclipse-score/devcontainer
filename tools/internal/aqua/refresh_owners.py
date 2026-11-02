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
"""Refresh aqua checksums and all generated native/Python compatibility views."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib
import urllib.request


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OWNER_DIR = ROOT / "tools/owners/aqua"
BOOTSTRAP = ROOT / "tools/internal/devcontainer/bootstrap_aqua.py"
BOOTSTRAP_PLATFORMS = (
    "linux/amd64",
    "linux/arm64",
    "darwin/amd64",
    "darwin/arm64",
)


def refresh_bootstrap_checksums(
    owner_dir: Path = OWNER_DIR, *, checksum_text: str | None = None
) -> None:
    """Refresh supported Aqua hashes while preserving unrelated TOML sections."""
    path = owner_dir / "aqua-bootstrap.toml"
    source = path.read_text(encoding="utf-8")
    manifest = tomllib.loads(source)
    version = manifest["version"]
    if checksum_text is None:
        url = (
            "https://github.com/aquaproj/aqua/releases/download/v"
            f"{version}/aqua_{version}_checksums.txt"
        )
        with urllib.request.urlopen(url) as response:
            checksum_text = response.read().decode("utf-8")
    checksums = {}
    for row in checksum_text.splitlines():
        fields = row.split()
        if len(fields) >= 2 and re.fullmatch(r"[a-fA-F0-9]{64}", fields[0]):
            checksums[fields[-1].removeprefix("*")] = fields[0].lower()
    missing_platforms = set(BOOTSTRAP_PLATFORMS) - manifest["archives"].keys()
    if missing_platforms:
        raise SystemExit(
            "Aqua bootstrap manifest is missing supported platforms: "
            + ", ".join(sorted(missing_platforms))
        )
    for platform in BOOTSTRAP_PLATFORMS:
        archive = manifest["archives"][platform]
        if archive["name"] not in checksums:
            raise SystemExit(f"Aqua release checksum file is missing {archive['name']}")

    pattern = re.compile(
        r'(?ms)(\[archives\."(?P<platform>[^"]+)"\]\s*'
        r'name = "(?P<name>[^"]+)"\s*sha256 = ")[^"]+("\s*)'
    )

    def replace(match: re.Match) -> str:
        platform = match.group("platform")
        if platform not in BOOTSTRAP_PLATFORMS:
            return match.group(0)
        archive = manifest["archives"][platform]
        if archive["name"] != match.group("name"):
            raise SystemExit(f"Unexpected archive name for Aqua platform {platform}")
        checksum = checksums[archive["name"]]
        return match.group(1) + checksum + match.group(4)

    updated, count = pattern.subn(replace, source)
    if count != len(manifest["archives"]):
        raise SystemExit("Could not parse every Aqua bootstrap archive section")
    if updated != source:
        path.write_text(updated, encoding="utf-8")


def refresh() -> None:
    """Refresh artifact data before deriving compatibility outputs from owners."""
    refresh_bootstrap_checksums()
    with tempfile.TemporaryDirectory(prefix="score-aqua-refresh-") as temporary:
        temporary_root = Path(temporary)
        environment = os.environ.copy()
        environment["AQUA_POLICY_CONFIG"] = str(OWNER_DIR / "aqua-policy.yaml")
        environment.setdefault("AQUA_ROOT_DIR", str(temporary_root / "aqua-root"))

        aqua = environment.get("AQUA_BINARY")
        if aqua is None:
            subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    "--output-dir",
                    str(temporary_root / "bootstrap"),
                    "--owner-dir",
                    str(OWNER_DIR),
                ],
                check=True,
            )
            aqua = str(temporary_root / "bootstrap/aqua")

        subprocess.run(
            [
                str(aqua),
                "-c",
                str(OWNER_DIR / "aqua.yaml"),
                "update-checksum",
                "--prune",
            ],
            check=True,
            env=environment,
        )
        subprocess.run(
            [sys.executable, str(HERE / "sync_repository.py")],
            check=True,
            cwd=ROOT,
        )
        subprocess.run(
            [sys.executable, str(ROOT / "tools/internal/sync_readme.py")],
            check=True,
            cwd=ROOT,
        )


if __name__ == "__main__":
    refresh()
