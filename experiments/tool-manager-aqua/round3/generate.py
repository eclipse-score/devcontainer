#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Produce static Python metadata and reuse the existing bounded Ruff export.

The authored Ruff decision stays in aqua.yaml. The copied native inputs are
release snapshots. setuptools builds the facade without running aqua; consumers
resolve its normal optional dependency and execute Ruff's own entrypoint.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("package_version")
parser.add_argument("output", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent
native = args.output / "native"
native.mkdir(parents=True, exist_ok=True)
for name in ["aqua.yaml", "aqua-checksums.json"]:
    shutil.copy2(root / name, native / name)
# Reuse the inspected first-round Ruff-specific recipe adapter unchanged. This
# is a bounded fixture copy, not another independently maintained recipe.
shutil.copy2(root.parent / "export_ruff_multitool.py", native / "export.py")
version = subprocess.check_output(
    [
        os.environ["AQUA_BINARY"],
        "-c",
        str(native / "aqua.yaml"),
        "which",
        "--version",
        "ruff",
    ],
    text=True,
).strip()
bazel = subprocess.check_output([sys.executable, str(native / "export.py")], text=True)
(args.output / "ruff.lock.json").write_text(bazel)
(
    args.output / "pyproject.toml"
).write_text(f'''# Generated from aqua.yaml; do not maintain a Ruff pin here.
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "score-aqua-tools-probe"
version = "{args.package_version}"
requires-python = ">=3.10"
license = "Apache-2.0"

[project.optional-dependencies]
ruff = ["ruff=={version}"]

[tool.setuptools]
packages = []
''')
(args.output / "selection.json").write_text(
    json.dumps(
        {
            "ruff": version,
            "facade_release": args.package_version,
            "owner": "round3/aqua.yaml",
            "bazel_version": json.loads(bazel)["ruff"]["version"],
        },
        indent=2,
    )
    + "\n"
)
print(json.dumps({"output": str(args.output), "ruff": version}))
