#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Generate ordinary package dependency metadata from the authoritative mise pin."""
import argparse
from pathlib import Path
import tomllib

parser = argparse.ArgumentParser()
parser.add_argument("release", type=Path)
parser.add_argument("package_version")
args = parser.parse_args()
version = tomllib.loads((args.release / "mise.native.toml").read_text())["tools"]["aqua:astral-sh/ruff"]
assert isinstance(version, str) and version[0].isdigit(), version
(args.release / "pyproject.toml").write_text(f'''# Generated from mise.native.toml; do not maintain Ruff pins here.
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "score-tools-probe"
version = "{args.package_version}"
requires-python = ">=3.10"

[project.optional-dependencies]
ruff = ["ruff=={version}"]

[tool.setuptools]
packages = []
''')
print("Generated standard metadata for", version)
