#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Bounded export probe: Ruff artifacts and the selected pre-commit definition.

Mise's lock owns artifact metadata. The Ruff archive layout below is additional
adapter knowledge; this probe is deliberately not a general packaging framework.
"""
import json
from pathlib import Path
import tomllib

root = Path(__file__).resolve().parent
config = tomllib.loads((root / "mise.python.toml").read_text())["tools"]
lock = tomllib.loads((root / "mise.native.lock").read_text())["tools"]
ruff = lock["aqua:astral-sh/ruff"][0]
output = root / "generated"
output.mkdir(exist_ok=True)
artifacts = []
for platform, artifact in ruff.items():
    if not platform.startswith("platforms."):
        continue
    system, cpu = platform.removeprefix("platforms.").split("-", 1)
    checksum_type, checksum = artifact["checksum"].split(":", 1)
    assert checksum_type == "sha256"
    archive = artifact["url"].rsplit("/", 1)[-1]
    assert archive.endswith(".tar.gz")
    artifacts.append({
        "kind": "archive",
        "file": archive.removesuffix(".tar.gz") + "/ruff",
        "url": artifact["url"],
        "sha256": checksum,
        "type": "tar.gz",
        "os": system,
        "cpu": {"x64": "x86_64", "arm64": "arm64"}[cpu],
    })
(output / "ruff.lock.json").write_text(json.dumps({"ruff": {
    "version": ruff["version"],
    "description": "Check and format Python code",
    "binaries": artifacts,
}}, indent=2) + "\n")
python_tools = {"pre-commit": {
    "package": "pre-commit",
    "version": config["pypi:pre-commit"],
    "entrypoint": "pre-commit",
    "description": "Run repository pre-commit hooks",
}}
(output / "python_tools.bzl").write_text(
    "# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation\n"
    "# SPDX-License-Identifier: Apache-2.0\n"
    "# Generated from mise.python.toml; do not maintain version pins here.\n"
    + "PYTHON_TOOLS = " + json.dumps(python_tools, indent=4) + "\n"
)
print("Exported Ruff lockfile and Python target metadata into", output)
