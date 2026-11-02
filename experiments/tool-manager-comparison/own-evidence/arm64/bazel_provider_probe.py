#!/usr/bin/env python3
"""Reproduce the failed ARM64 provider boundary, not a fresh-image substitute."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

root = Path("/home/alex/git/etas-contrib/score_devcontainer-eval-own")
task = Path("/tmp/score-own-copilot")
output = task / "arm64/bazel-provider"
output.mkdir()
output.chmod(0o777)
home = output / "home"
home.mkdir()
home.chmod(0o777)
prefix = task / "arm64/prepared"
command = [
    "docker", "run", "--rm", "--name", "score-own-arm64-bazel-provider",
    "--label", "score-own-platform.candidate=own", "--platform", "linux/arm64",
    "--read-only", "--user", "1000:1000", "--tmpfs", "/tmp:rw,mode=1777",
    "-v", str(prefix) + ":" + str(prefix) + ":ro",
    "-v", str(output) + ":" + str(output),
    "-e", "HOME=" + str(home), "-e", "USE_BAZEL_VERSION=8.6.0",
    "--workdir", "/tmp", "--entrypoint", str(prefix / "bin/bazelisk"),
    "score-tooling-reference:final-arm64", "--batch", "version",
]
records = []
for attempt in range(1, 4):
    started = time.monotonic()
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    records.append({
        "attempt": attempt, "argv": command, "exit": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr,
        "elapsed_seconds": round(time.monotonic() - started, 2),
    })
    if result.returncode == 0:
        assert "Build label: 8.6.0" in result.stdout, result.stdout
        break
    time.sleep(2)
online = result.returncode == 0
offline = None
if online:
    offline_command = command[:3] + ["--network", "none"] + command[3:]
    result = subprocess.run(offline_command, capture_output=True, text=True, timeout=300)
    offline = {"argv": offline_command, "exit": result.returncode,
               "stdout": result.stdout, "stderr": result.stderr}
    assert result.returncode == 0 and "Build label: 8.6.0" in result.stdout, offline
report = {
    "status": "passed" if online else "failed", "online_attempts": records,
    "offline_warm_cache": offline,
    "source_sha256": {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest()
        for path in ("tools/providers.json", "tools/lockfiles/bazelisk.lock.json")
    },
    "boundary": "Targeted recovery/reproduction of existing Bazel-engine provider download in isolated uid-1000 cache. Cached OS substrate, newly prepared Bazelisk; not a fresh-image or full-suite pass.",
}
(output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
print(output / "result.json")
raise SystemExit(0 if online else 1)
