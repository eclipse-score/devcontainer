#!/usr/bin/env python3
"""Task-only ARM64 prepared-output gate; no source or artifact overrides."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path("/home/alex/git/etas-contrib/score_devcontainer-eval-own")
TASK = Path("/tmp/score-own-copilot")
OUTPUT = TASK / "arm64"
PREFIX = OUTPUT / "prepared"
IMAGE = "score-tooling-reference:final-arm64"
OUTPUT.mkdir(exist_ok=True)
PREFIX.mkdir(exist_ok=True)


def hashes():
    paths = [
        *sorted((ROOT / "tools/lockfiles").glob("*.lock.json")),
        ROOT / "tools/score_tools/catalog.py",
        ROOT / "tools/score_tools/provision.py",
        ROOT / "tools/score_tools/python_tools.bzl",
        ROOT / "tools/internal/provision.py",
        ROOT / "tools/tests/prepared_smoke.py",
        ROOT / "tools/run-tool",
    ]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in paths}


def run(mode, command, timeout):
    log = OUTPUT / (mode + ".log")
    started = time.monotonic()
    before = hashes()
    with log.open("w") as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
        reason = None
        while process.poll() is None:
            if shutil.disk_usage(TASK).free < 4 * 1024**3:
                reason = "free disk below 4 GiB"
            elif time.monotonic() - started > timeout:
                reason = f"timeout after {timeout} seconds"
            if reason:
                subprocess.run(["docker", "stop", "--time", "10",
                                "score-own-arm64-" + mode], check=False,
                               stdout=stream, stderr=subprocess.STDOUT)
                process.wait(timeout=30)
                break
            time.sleep(2)
    record = {
        "mode": mode, "argv": command, "exit": process.returncode,
        "status": "passed" if process.returncode == 0 and not reason else "failed",
        "stop_reason": reason, "elapsed_seconds": round(time.monotonic() - started, 2),
        "source_sha256": before, "source_unchanged": hashes() == before,
        "substrate_image": subprocess.check_output(
            ["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"],
            text=True).strip(),
        "log": str(log),
    }
    if not record["source_unchanged"]:
        record["status"] = "failed"
    (OUTPUT / (mode + ".json")).write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return 0 if record["status"] == "passed" else 1


mode = sys.argv[1]
common = [
    "docker", "run", "--rm", "--name", "score-own-arm64-" + mode,
    "--label", "score-own-platform.candidate=own", "--platform", "linux/arm64",
    "--read-only", "--tmpfs", "/tmp:rw,mode=1777",
    "-v", str(ROOT / "tools") + ":/own-tools:ro",
    "-v", str(OUTPUT) + ":" + str(OUTPUT),
]
if mode == "prepare":
    command = [
        *common, "-e", "PYTHONDONTWRITEBYTECODE=1",
        "-e", "UV_PYTHON=/usr/bin/python3",
        "-e", "UV_CACHE_DIR=" + str(OUTPUT / "cache"),
        "--entrypoint", "/usr/bin/python3", IMAGE,
        "/own-tools/internal/provision.py", "published",
        "--prefix", str(PREFIX),
        "--native", "actionlint", "apm", "bazelisk", "buildifier", "opencode",
        "ruff", "shellcheck", "starpls", "uv", "uvx", "yamlfmt",
        "--python", "basedpyright", "pre-commit", "pytest",
    ]
    raise SystemExit(run(mode, command, 1200))
if mode == "check":
    evidence = OUTPUT / "offline"
    evidence.mkdir()
    evidence.chmod(0o777)
    command = [
        *common, "--network", "none", "--user", "1000:1000",
        "-v", str(PREFIX) + ":" + str(PREFIX) + ":ro",
        "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
        "--entrypoint", "/usr/bin/python3", IMAGE,
        "/own-tools/tests/prepared_smoke.py", "--prefix", str(PREFIX),
        "--output", str(evidence / "prepared.json"),
    ]
    raise SystemExit(run(mode, command, 1200))
if mode == "inspect":
    command = [
        *common, "--network", "none", "--user", "1000:1000",
        "-v", str(PREFIX) + ":" + str(PREFIX) + ":ro",
        "-v", str(TASK / "arm64_inspect.py") + ":/arm64_inspect.py:ro",
        "-e", "HOME=/tmp", "-e", "PYTHONDONTWRITEBYTECODE=1",
        "--entrypoint", "/usr/bin/python3", IMAGE, "/arm64_inspect.py",
        str(PREFIX), str(OUTPUT / "offline/architecture.json"),
    ]
    raise SystemExit(run(mode, command, 120))
raise SystemExit("Expected prepare, check or inspect")
