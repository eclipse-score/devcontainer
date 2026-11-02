#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Shared behavioral fixture for host selection and prepared direct execution."""

import json
import os
from pathlib import Path
import subprocess
import tempfile

ruff = json.loads(os.environ["TEST_RUFF_COMMAND"])
pre_commit = json.loads(os.environ["TEST_PRE_COMMIT_COMMAND"])
results = {"uid": os.getuid(), "ruff_command": ruff, "pre_commit_command": pre_commit}
with tempfile.TemporaryDirectory(prefix="aqua consumer ") as temporary:
    root = Path(temporary)
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    fake = root / "wrong-bin"
    fake.mkdir()
    for command in ["ruff", "pre-commit"]:
        path = fake / command
        path.write_text("#!/bin/sh\necho WRONG_TOOL\nexit 99\n")
        path.chmod(0o755)
    (root / "aqua.yaml").write_text("packages:\n  - name: astral-sh/ruff@0.11.12\n")
    (root / "pyproject.toml").write_text(
        '[project]\nname="conflicting-consumer"\nversion="0.0.0"\ndependencies=["pre-commit==4.5.1"]\n'
    )
    env = {**os.environ, "PATH": str(fake) + ":" + os.environ["PATH"]}
    for name, command, expected in [
        ("ruff", ruff, "0.11.13"),
        ("pre-commit", pre_commit, "4.7.0"),
    ]:
        run = subprocess.run(
            command + ["--version"], cwd=root, env=env, capture_output=True, text=True
        )
        assert run.returncode == 0 and expected in run.stdout, (
            name,
            run.stdout,
            run.stderr,
        )
        results[name + "_version"] = run.stdout.strip()
    fixture = root / "file with spaces.py"
    fixture.write_text("import os\n")
    run = subprocess.run(
        ruff + ["check", "--isolated", "--output-format", "json", fixture.name],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    diagnostics = json.loads(run.stdout)
    assert run.returncode == 1 and diagnostics[0]["code"] == "F401", run
    assert diagnostics[0]["filename"] == str(fixture), diagnostics
    results["ruff_result"] = {
        "exit": run.returncode,
        "code": diagnostics[0]["code"],
        "filename": diagnostics[0]["filename"],
    }
    (root / "observe.py").write_text(
        'import json, os, pathlib, sys\npathlib.Path("observed.json").write_text(json.dumps({"cwd":os.getcwd(), "args":sys.argv[1:]}))\nsys.exit(7)\n'
    )
    (root / ".pre-commit-config.yaml").write_text(
        'repos:\n  - repo: local\n    hooks:\n      - id: observe\n        name: observe caller\n        language: system\n        entry: python3 observe.py\n        args: ["two words", "--literal=one two"]\n        always_run: true\n        pass_filenames: false\n'
    )
    run = subprocess.run(
        pre_commit + ["run", "--all-files"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
    )
    observed = json.loads((root / "observed.json").read_text())
    assert observed == {"cwd": str(root), "args": ["two words", "--literal=one two"]}, (
        observed
    )
    assert run.returncode == 1 and "exit code: 7" in run.stdout, (
        run.stdout,
        run.stderr,
    )
    results["pre_commit_result"] = {
        "exit": run.returncode,
        "hook_exit": 7,
        "observed": observed,
    }
    results["consumer_config_ignored"] = True
    results["wrong_path_binaries_ignored"] = True
print(json.dumps(results, indent=2))
