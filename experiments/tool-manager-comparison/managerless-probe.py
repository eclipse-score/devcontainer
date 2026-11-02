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
"""Probe ordinary Python metadata delivery from existing pins, without a manager.

This bounded Ruff fixture does not migrate production packaging or demonstrate
native host installation. All generated artifacts stay below --output.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "tools"))
    from score_tools.catalog import _load_python_tools

    requirements = {
        name: f"{item['package']}=={item['version']}"
        for name, item in _load_python_tools().items()
    }
    ruff = json.loads((root / "tools/lockfiles/ruff.lock.json").read_text())["ruff"][
        "version"
    ]
    requirements["ruff"] = f"ruff=={ruff}"
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("This probe requires ordinary uv on PATH")
    env = {**os.environ, "UV_NO_CONFIG": "1"}
    records = []

    def run(argv, cwd=output, expected=0):
        result = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True)
        records.append(
            {
                "argv": list(map(str, argv)),
                "exit": result.returncode,
                "stdout": result.stdout[-3000:],
                "stderr": result.stderr[-3000:],
            }
        )
        if result.returncode != expected:
            raise RuntimeError(records[-1])
        return result.stdout

    package = output / "package"
    package.mkdir(exist_ok=True)
    metadata = (
        '[build-system]\nrequires = ["setuptools>=68"]\n'
        'build-backend = "setuptools.build_meta"\n\n'
        '[project]\nname = "score-managerless-probe"\nversion = "0.1.0"\n'
        'requires-python = ">=3.11"\n\n[project.optional-dependencies]\n'
    )
    for name, requirement in sorted(requirements.items()):
        metadata += f"{json.dumps(name)} = [{json.dumps(requirement)}]\n"
    metadata += "\n[tool.setuptools]\npackages = []\n"
    (package / "pyproject.toml").write_text(metadata)
    run([uv, "build", "--wheel", str(package), "--out-dir", str(output / "dist")])
    wheel = output / "dist/score_managerless_probe-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel) as archive:
        wheel_metadata = archive.read(
            "score_managerless_probe-0.1.0.dist-info/METADATA"
        ).decode()
    consumer = output / "consumer"
    consumer.mkdir(exist_ok=True)
    dependency = f"score-managerless-probe[ruff] @ {wheel.as_uri()}"
    (consumer / "pyproject.toml").write_text(
        '[project]\nname = "probe-consumer"\nversion = "0.1.0"\n'
        'requires-python = ">=3.11"\n'
        f"dependencies = [{json.dumps(dependency)}]\n"
    )
    run([uv, "lock", "--python", sys.executable], cwd=consumer)
    run([uv, "sync", "--locked"], cwd=consumer)
    assert run([uv, "run", "--locked", "ruff", "--version"], cwd=consumer).strip() == (
        f"ruff {ruff}"
    )
    assert run(
        [uv, "tool", "run", "--with", dependency, "ruff", "--version"]
    ).strip() == (f"ruff {ruff}")
    direct = consumer / ".venv/bin/ruff"
    assert run([str(direct), "--version"]).strip() == f"ruff {ruff}"
    fixture = consumer / "undefined.py"
    fixture.write_text("print(undefined_name)\n")
    diagnostic = run(
        [
            str(direct),
            "check",
            "--isolated",
            "--no-cache",
            "--select",
            "F821",
            str(fixture),
        ],
        expected=1,
    )
    assert "F821" in diagnostic and "undefined_name" in diagnostic
    evidence = {
        "result": "passed",
        "scope": "Existing-catalog Ruff facade and ordinary consumer; not a fourth migration",
        "network": "Host network allowed; existing uv cache may be reused; no timing claim",
        "requirements": requirements,
        "requires_dist": [
            line
            for line in wheel_metadata.splitlines()
            if line.startswith("Requires-Dist:")
        ],
        "consumer_supplies_separate_ruff_pin": False,
        "package_contains_runner": False,
        "commands": records,
        "limits": [
            "Only Ruff extra executed; other extras inspected as metadata only",
            "No native-host provisioning, all-platform, release-publication or image proof",
            "No startup measurement or network isolation performed",
        ],
    }
    (output / "proof.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"Passed: {output / 'proof.json'}")


if __name__ == "__main__":
    main()
