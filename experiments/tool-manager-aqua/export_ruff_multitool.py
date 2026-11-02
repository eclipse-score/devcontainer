#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Bounded bridge probe: export aqua-resolved Ruff release to rules_multitool.

This deliberately supports only Ruff's known GitHub tarball layout. It is not a
universal registry translator. Other tools would need compatible recipe export
or their own layout mapping. Versions and digests come from aqua, not this file.
"""

import json
import os
from pathlib import Path
import subprocess
import sys

config = Path(__file__).with_name("aqua.yaml")
aqua = os.environ["AQUA_BINARY"]
version = subprocess.check_output(
    [aqua, "-c", str(config), "which", "--version", "ruff"], text=True
).strip()
prefix = f"github_release/github.com/astral-sh/ruff/{version}/"
binaries = []
for item in json.loads(config.with_name("aqua-checksums.json").read_text())[
    "checksums"
]:
    if not item["id"].startswith(prefix):
        continue
    archive = item["id"][len(prefix) :]
    cpu = "arm64" if "aarch64" in archive else "x86_64"
    system = "macos" if "apple-darwin" in archive else "linux"
    binaries.append(
        {
            "kind": "archive",
            "file": archive.removesuffix(".tar.gz") + "/ruff",
            "url": f"https://github.com/astral-sh/ruff/releases/download/{version}/{archive}",
            "sha256": item["checksum"].lower(),
            "type": "tar.gz",
            "os": system,
            "cpu": cpu,
        }
    )
if not binaries:
    raise SystemExit("No Ruff release checksums; run aqua update-checksum first")
json.dump(
    {
        "ruff": {
            "version": version,
            "description": "Check and format Python",
            "binaries": binaries,
        }
    },
    sys.stdout,
    indent=2,
)
print()
