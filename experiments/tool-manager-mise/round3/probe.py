#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Ruff authority -> native/Bazel metadata -> normal uv dependency and uvx."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib

root = Path(__file__).resolve().parent
previous = root.parent
state = Path(tempfile.mkdtemp(prefix="round3-package-", dir="/tmp/score-mise-evaluation"))
producer = state / "producer"
consumer = state / "consumer"
producer.mkdir()
consumer.mkdir()
uv = Path(shutil.which("uv")).resolve()
uvx = Path(shutil.which("uvx")).resolve()
environment = {**os.environ, "UV_CACHE_DIR": str(state / "uv-cache"),
               "UV_PYTHON_INSTALL_DIR": str(state / "uv-python"),
               "UV_PYTHON_DOWNLOADS": "never", "UV_PYTHON": "/usr/bin/python3",
               "PATH": "/usr/bin:/bin"}
evidence = {"state": str(state), "uv": str(uv), "uvx": str(uvx), "commands": [], "releases": []}


def run(argv, *, cwd=producer, env=None):
    result = subprocess.run([str(arg) for arg in argv], cwd=cwd, env=env,
                            text=True, capture_output=True)
    entry = {"argv": [str(a) for a in argv], "cwd": str(cwd), "status": result.returncode,
             "stdout": result.stdout, "stderr": result.stderr}
    evidence["commands"].append(entry)
    if result.returncode:
        (root / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
        raise RuntimeError(entry)
    return result.stdout


for name in ("mise.toml", "mise.native.toml", "mise.native.lock", "mise.python.toml", "mise.repository.toml", "export-bazel.py"):
    shutil.copy2(previous / name, producer / name)
run(["git", "init", "-q"])
(consumer / "pyproject.toml").write_text('[project]\nname="round3-consumer"\nversion="0.0.0"\nrequires-python=">=3.10"\ndependencies=[]\n')
for index, release in enumerate(("0.1.0", "0.2.0")):
    if index:
        run([previous / "mise-probe", "-C", producer, "use", "--env", "native", "--pin", "aqua:astral-sh/ruff@0.11.12"])
    selected = tomllib.loads((producer / "mise.native.toml").read_text())["tools"]["aqua:astral-sh/ruff"]
    native = run([previous / "release-run", producer, "ruff", "--version"])
    assert native.strip() == "ruff " + selected
    run(["python3", producer / "export-bazel.py"])
    bazel = json.loads((producer / "generated/ruff.lock.json").read_text())["ruff"]
    assert bazel["version"] == selected
    run(["python3", root / "generate-package.py", producer, release])
    run(["git", "add", "."])
    run(["git", "-c", "user.name=Probe", "-c", "user.email=probe@example.invalid", "commit", "-qm", "Generated release " + release])
    run(["git", "tag", "v" + release])
    revision = run(["git", "rev-parse", "HEAD"]).strip()
    spec = f"score-tools-probe[ruff] @ git+{producer.as_uri()}@v{release}"
    run([uv, "add", "--raw", spec], cwd=consumer, env=environment)
    run([uv, "lock", "--check"], cwd=consumer, env=environment)
    run([uv, "sync", "--locked"], cwd=consumer, env=environment)
    project_output = run([uv, "run", "--locked", "ruff", "--version"], cwd=consumer, env=environment)
    assert project_output.strip() == "ruff " + selected
    requires_dist = run([uv, "run", "--locked", "python", "-c",
                        "import importlib.metadata as m; print(m.metadata('score-tools-probe').get_all('Requires-Dist'))"],
                       cwd=consumer, env=environment)
    assert "ruff==" + selected in requires_dist
    uvx_output = run([uvx, "--from", spec, "ruff", "--version"], cwd=consumer, env=environment)
    assert uvx_output.strip() == "ruff " + selected
    uvx_with = run([uvx, "--with", spec, "ruff", "--version"], cwd=consumer, env=environment)
    assert uvx_with.strip() == "ruff " + selected
    assert "warning:" not in evidence["commands"][-1]["stderr"]
    uv_lock = tomllib.loads((consumer / "uv.lock").read_text())
    locked_ruff = next(p for p in uv_lock["package"] if p["name"] == "ruff")
    assert locked_ruff["version"] == selected
    project = tomllib.loads((consumer / "pyproject.toml").read_text())
    assert project["project"]["dependencies"] == [spec]
    snapshot = root / ("before" if index == 0 else "after")
    snapshot.mkdir(exist_ok=True)
    for source, name in ((producer / "mise.native.toml", "mise.native.toml"),
                         (producer / "mise.native.lock", "mise.native.lock"),
                         (producer / "pyproject.toml", "package.pyproject.toml"),
                         (producer / "generated/ruff.lock.json", "ruff.lock.json"),
                         (consumer / "pyproject.toml", "consumer.pyproject.toml"),
                         (consumer / "uv.lock", "consumer.uv.lock")):
        shutil.copy2(source, snapshot / name)
    evidence["releases"].append({"package_version": release, "tag": "v" + release,
        "commit": revision, "authoritative_ruff": selected, "native": native.strip(),
        "bazel_metadata_version": bazel["version"], "uv_project": project_output.strip(),
        "uv_locked_ruff": locked_ruff["version"], "requires_dist": requires_dist.strip(),
        "uvx": uvx_output.strip(), "uvx_with": uvx_with.strip(), "consumer_requirement": spec})
(root / "authoritative.diff").write_text(run(["git", "diff", "v0.1.0", "v0.2.0", "--", "mise.native.toml"]))
(root / "generated.diff").write_text(run(["git", "diff", "v0.1.0", "v0.2.0", "--", "mise.native.lock", "generated/ruff.lock.json", "pyproject.toml"]))
(root / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
(root / "state-path.txt").write_text(str(state) + "\n")
print(json.dumps(evidence["releases"], indent=2))
