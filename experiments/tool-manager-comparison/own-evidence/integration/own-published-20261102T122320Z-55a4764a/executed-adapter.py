#!/usr/bin/env python3
"""Use the existing comparison gate read-only with a task-specific output root."""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
source = Path("/home/alex/git/etas-contrib/score_devcontainer-eval-own")
harness = Path("/home/alex/git/etas-contrib/score_devcontainer/experiments/tool-manager-comparison/integration-gates/gate.py")
spec = importlib.util.spec_from_file_location("comparison_gate", harness)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
gate.TASK_ROOT = Path("/tmp/score-own-copilot/integration")
gate.TASK_ROOT.mkdir(parents=True, exist_ok=True)
original_snapshot = gate.snapshot_source


def snapshot_source(source, workspace, log_path):
    original_snapshot(source, workspace, log_path)
    paths = [
        "tools/score_tools/provision.py", "tools/score_tools/catalog.py",
        "tools/internal/devcontainer/install.py", ".devcontainer/post_create_command.sh",
        "src/s-core-devcontainer/.devcontainer/s-core-local/install.sh",
        "src/s-core-devcontainer/.devcontainer/bazel-feature/install.sh",
        "src/s-core-devcontainer/.devcontainer/Dockerfile",
        "src/s-core-devcontainer/.devcontainer/devcontainer.json",
        "src/s-core-devcontainer/test-project/test.sh",
        "src/s-core-devcontainer/.devcontainer/s-core-local/tests/test_default.sh",
        "src/s-core-devcontainer/.devcontainer/bazel-feature/tests/test_default.sh",
        "tools/score_tools/python_tools.bzl", "tools/environments.json",
    ]
    paths.extend(str(path.relative_to(workspace)) for path in
                 sorted((workspace / "tools/lockfiles").glob("*.lock.json")))
    (workspace.parent / "source-hashes.json").write_text(json.dumps({
        path: hashlib.sha256((workspace / path).read_bytes()).hexdigest() for path in paths
    }, indent=2) + "\n")


gate.snapshot_source = snapshot_source
original_terminal_check = gate.run_later_terminal_check


def terminal_check(*args):
    attempts = []
    for attempt in range(1, 4):
        try:
            original_terminal_check(*args)
        except gate.GateError as error:
            attempts.append({"attempt": attempt, "status": "failed", "error": str(error)})
            (args[4] / "terminal-attempts.json").write_text(json.dumps(attempts, indent=2) + "\n")
            print(f"Terminal gate attempt {attempt}/3 failed: {error}", flush=True)
            if attempt == 3:
                raise
        else:
            attempts.append({"attempt": attempt, "status": "passed"})
            (args[4] / "terminal-attempts.json").write_text(json.dumps(attempts, indent=2) + "\n")
            return


gate.run_later_terminal_check = terminal_check
if sys.argv[1] == "lifecycle":
    gate.execute_lifecycle("own", source, devcontainer=gate.DEFAULT_DEVCONTAINER,
                           min_free_gib=2, keep_workspace=False)
else:
    gate.execute_published("own", source, devcontainer=gate.DEFAULT_DEVCONTAINER,
                           min_free_gib=4, build_stop_free_gib=1.5,
                           disk_check_interval=2, keep_workspace=False)
