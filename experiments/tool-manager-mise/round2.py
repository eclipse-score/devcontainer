#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Reproduce bounded C1/C2 checks; all release copies are temporary fixtures."""
import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parent
probe = root / "mise-probe"
runner = root / "release-run"
evidence = []


def run(args, *, cwd=None, env=None, expected=0):
    result = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    item = {"argv": [str(a) for a in args], "cwd": str(cwd), "status": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}
    evidence.append(item)
    assert result.returncode == expected, item
    return result.stdout


with tempfile.TemporaryDirectory(prefix="round2-", dir="/tmp/score-mise-evaluation") as temporary:
    state = Path(temporary)
    release = state / "release"
    release.mkdir()
    for source in root.glob("mise.*"):
        if source.suffix in (".toml", ".lock"):
            shutil.copy2(source, release / source.name)
    before = {p.name: p.read_text() for p in release.iterdir()}
    run([probe, "-C", release, "use", "--env", "native", "--pin", "aqua:astral-sh/ruff@0.11.12"])
    assert "ruff 0.11.12" in run([runner, release, "ruff", "--version"], cwd=state)
    assert "pre-commit 4.7.0" in run([runner, release, "pre-commit", "--version"], cwd=state)
    diff = "".join("".join(difflib.unified_diff(before.get(p.name, "").splitlines(True),
        p.read_text().splitlines(True), fromfile="before/"+p.name, tofile="after/"+p.name))
        for p in release.iterdir())
    (root / "round2-maintenance.diff").write_text(diff)
    assert (release / "mise.python.toml").read_text() == before["mise.python.toml"]

    consumer = state / "external consumer" / "nested checkout"
    consumer.mkdir(parents=True)
    run(["git", "init", "-q", consumer])
    (consumer / "mise.toml").write_text('[tools]\n"aqua:astral-sh/ruff"="0.0.0"\n"pypi:pre-commit"="0.0.0"\n')
    fake = consumer / "fake-bin"
    fake.mkdir()
    marker = state / "poison-called"
    for name in ("ruff", "pre-commit"):
        tool = fake / name
        tool.write_text(f'#!/bin/sh\ntouch "{marker}"\necho POISON\nexit 97\n')
        tool.chmod(0o755)
    environment = {**os.environ, "PATH": str(fake)+":"+os.environ["PATH"],
                   "EXPECTED_CWD": str(consumer), "PRE_COMMIT_HOME": str(state / "pre-commit")}
    # release-run preserves this PATH into mise, whose selected tool paths
    # must precede the deliberately conflicting host executables.
    environment["MISE_ENV"] = "native,python"
    assert "ruff 0.11.12" in run([runner, release, "ruff", "--version"], cwd=consumer, env=environment)
    fixture = consumer / "fixture with space.py"
    fixture.write_text("import os\n")
    run([runner, release, "ruff", "check", "--isolated", fixture.name], cwd=consumer,
        env=environment, expected=1)
    fixture.write_text('print("ready")\n')
    run(["git", "add", fixture.name], cwd=consumer)
    (consumer / ".pre-commit-config.yaml").write_text('''repos:
  - repo: local
    hooks:
      - id: observe-cwd
        name: Observe consumer cwd
        language: system
        entry: >-
          python3 -c 'import os,sys; print(os.getcwd()); assert os.getcwd()==os.environ["EXPECTED_CWD"]; assert sys.argv[1:]==["marker value"]' 'marker value'
        pass_filenames: false
''')
    assert "pre-commit 4.7.0" in run([runner, release, "pre-commit", "--version"], cwd=consumer, env=environment)
    run([runner, release, "pre-commit", "run", "observe-cwd", "--all-files", "--verbose"], cwd=consumer, env=environment)
    # Exercise a real pre-commit failure as well, not only a successful hook.
    config = consumer / ".pre-commit-config.yaml"
    config.write_text(config.read_text().replace('marker value\'\n', 'wrong value\'\n'))
    run([runner, release, "pre-commit", "run", "observe-cwd", "--all-files"], cwd=consumer, env=environment, expected=1)
    assert not marker.exists(), "an arbitrary host executable was selected"
(root / "round2-evidence.json").write_text(json.dumps(evidence, indent=2)+"\n")
print("C1/C2 evidence:", len(evidence), "real commands completed")
