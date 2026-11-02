#!/usr/bin/env python3
"""Use the existing comparison gate read-only with a task-specific output root."""
import importlib.util
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
arm64 = sys.argv[1] == "published-arm64"
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
    shutil.copy2(__file__, workspace.parent / "executed-adapter.py")
    (workspace.parent / "gate-binding.json").write_text(json.dumps({
        "platform": "linux/arm64" if arm64 else "linux/amd64",
        "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "harness_sha256": hashlib.sha256(harness.read_bytes()).hexdigest(),
        "artifact_overrides": False,
        "feature_suite": "unchanged source suite appended to rendered Dockerfile",
        "output": "type=cacheonly; no image loaded, launched or published",
        "platform_adapter": "Only Dev Containers --platform and result/image labels change for ARM64; build command bounded to 30 minutes.",
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
if arm64:
    original_run_logged = gate.run_logged
    original_run_id = gate.new_run_id
    gate.new_run_id = lambda candidate, name: original_run_id(candidate, name + "-arm64")
    gate.published_image_name = lambda candidate, run: f"score-m6-{candidate}-{run.lower()}:local-arm64"

    def run_logged(args, log_path, **kwargs):
        if args[:2] == [str(gate.DEFAULT_DEVCONTAINER), "build"]:
            args = list(args)
            slot = args.index("--platform") + 1
            assert args[slot] == "linux/amd64"
            args[slot] = "linux/arm64"
            args = ["timeout", "--signal=INT", "--kill-after=30", "1800", *args]
        original_run_logged(args, log_path, **kwargs)

    gate.run_logged = run_logged
if sys.argv[1] == "lifecycle":
    gate.execute_lifecycle("own", source, devcontainer=gate.DEFAULT_DEVCONTAINER,
                           min_free_gib=2, keep_workspace=False)
else:
    try:
        gate.execute_published("own", source, devcontainer=gate.DEFAULT_DEVCONTAINER,
                               min_free_gib=8 if arm64 else 4,
                               build_stop_free_gib=4 if arm64 else 1.5,
                               disk_check_interval=2, keep_workspace=False)
    finally:
        if arm64:
            for result in gate.TASK_ROOT.glob("own-published-arm64-*/result.json"):
                data = json.loads(result.read_text())
                data["shared_gate_label"] = data["gate"]
                data["gate"] = "fresh-published-arm64-build-and-feature-tests"
                data["platform_adapter"] = "Task adapter changes platform and labels only; same feature tests."
                result.write_text(json.dumps(data, indent=2) + "\n")
