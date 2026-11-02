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
"""Run the task-scoped M6 Dev Container integration gates."""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from shlex import join as shell_join, quote as shell_quote


TASK_ROOT = Path("/tmp/score-m6-gates")
DEFAULT_DEVCONTAINER = Path("/tmp/score-m5-nix/bin/devcontainer")
NIX_ARTIFACTS_ROOT = Path("/tmp/score-m6-nix")
NIX_RELEASE = NIX_ARTIFACTS_ROOT / "release-amd64"
CANDIDATES = ("mise", "aqua", "nix")
READINESS_FILES = {
    "nix": Path("/tmp/score-m6-integration-20261102/nix.last.md"),
    "mise": Path("/tmp/score-m6-integration-20261102/mise.review.last.md"),
    "aqua": Path("/tmp/score-m6-integration-20261102/aqua.review.last.md"),
}
LIFECYCLE_FIX_READINESS_FILES = {
    "mise": Path("/tmp/score-m6-integration-20261102/mise.lifecycle-fix.last.md"),
    "aqua": Path("/tmp/score-m6-integration-20261102/aqua.lifecycle-fix.last.md"),
}
NIX_RELEASE_READINESS = Path("/tmp/score-m6-integration-20261102/nix.release.last.md")
GIB = 1024**3
DEFAULT_MIN_FREE_GIB = 4.0
DEFAULT_BUILD_STOP_FREE_GIB = 1.5
DEFAULT_DISK_CHECK_INTERVAL = 2.0


class GateError(RuntimeError):
    """A gate stopped before its evidence could be reported as passing."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run M6 integration gates. `run` executes; add --dry-run to print "
            "the plan without reading candidate source or contacting Docker."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="run one candidate's gates")
    run_parser.add_argument("--candidate", choices=CANDIDATES, required=True)
    run_parser.add_argument(
        "--source",
        type=Path,
        help=(
            "candidate source worktree (defaults to "
            "/home/alex/git/etas-contrib/score_devcontainer-eval-CANDIDATE)"
        ),
    )
    run_parser.add_argument(
        "--gate", choices=("all", "lifecycle", "published"), default="all"
    )
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--keep-workspace", action="store_true")
    run_parser.add_argument("--min-free-gib", type=float, default=DEFAULT_MIN_FREE_GIB)
    run_parser.add_argument(
        "--build-stop-free-gib", type=float, default=DEFAULT_BUILD_STOP_FREE_GIB
    )
    run_parser.add_argument(
        "--disk-check-interval", type=float, default=DEFAULT_DISK_CHECK_INTERVAL
    )

    all_parser = subparsers.add_parser(
        "run-all", help="run all candidates serially in mise, aqua, Nix order"
    )
    all_parser.add_argument(
        "--gate", choices=("all", "lifecycle", "published"), default="all"
    )
    all_parser.add_argument("--dry-run", action="store_true")
    all_parser.add_argument("--keep-workspace", action="store_true")
    all_parser.add_argument("--min-free-gib", type=float, default=DEFAULT_MIN_FREE_GIB)
    all_parser.add_argument(
        "--build-stop-free-gib", type=float, default=DEFAULT_BUILD_STOP_FREE_GIB
    )
    all_parser.add_argument(
        "--disk-check-interval", type=float, default=DEFAULT_DISK_CHECK_INTERVAL
    )

    return parser.parse_args()


def candidate_source(candidate: str, override: Path | None = None) -> Path:
    path = override or Path(
        f"/home/alex/git/etas-contrib/score_devcontainer-eval-{candidate}"
    )
    return path.expanduser().resolve()


def new_run_id(candidate: str, gate_name: str) -> str:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"{candidate}-{gate_name}-{stamp}-{uuid.uuid4().hex[:8]}"


def published_image_name(candidate: str, run_id: str) -> str:
    return f"score-m6-{candidate}-{run_id.lower()}:local-amd64"


def append_progress(message: str) -> None:
    progress_path = TASK_ROOT / "progress.md"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    with progress_path.open("a") as progress:
        progress.write(f"\n- [{timestamp}] {message}\n")


def candidate_readiness(candidate: str, gate: str) -> Path:
    if candidate in LIFECYCLE_FIX_READINESS_FILES:
        return LIFECYCLE_FIX_READINESS_FILES[candidate]
    if candidate == "nix" and gate == "published":
        return NIX_RELEASE_READINESS
    return READINESS_FILES[candidate]


def candidate_ready(candidate: str, gate: str) -> bool:
    path = candidate_readiness(candidate, gate)
    return path.is_file() and bool(path.read_text().strip())


def print_plan(
    candidate: str,
    source: Path,
    gate: str,
    min_free_gib: float,
    build_stop_free_gib: float,
    disk_check_interval: float,
) -> None:
    print(f"Candidate: {candidate}")
    print(f"Read-only source worktree: {source}")
    print(f"Task output root: {TASK_ROOT}")
    print(f"Minimum free disk before a gate: {min_free_gib:g} GiB")
    print("Execution: dry-run only; no source or Docker state is inspected.")
    if gate in ("all", "lifecycle"):
        print("\nRoot generic Node lifecycle:")
        print(
            "  copy source while excluding Git metadata and named caches/runtime payloads"
        )
        print("  initialize a task-local .git so pre-commit cannot touch source hooks")
        print(
            "  devcontainer up --workspace-folder <copy> --id-label "
            "score-m6-gates.run=<run-id>"
        )
        print("  run current docker-in-docker feature and postCreateCommand")
        print(
            "  start a new interactive shell; verify uv/uvx/ruff/pre-commit, "
            "hook, DinD daemon and builder"
        )
        print("  remove only containers carrying that exact task label")
        print("  remove only newly created volumes mounted by those task containers")
        print("  remove only image tags observed from this temporary workspace build")
    if gate in ("all", "published"):
        print("\nFresh published amd64 build plus existing feature tests:")
        if candidate == "nix":
            print(
                "  SCORE_NIX_PREPARED_RELEASE="
                f"{NIX_RELEASE} TMPDIR=<task-run-dir> bash "
                "scripts/build.sh --amd64 score-m6-nix-<run-id>"
            )
            print(
                "  Nix build script validates the retained release, stages one isolated context, and calls a task CLI shim"
            )
        print(
            "  devcontainer build --workspace-folder <copy>/src/s-core-devcontainer "
            "--image-name score-m6-<candidate>-<run-id>:local-amd64 "
            "--platform linux/amd64 --no-cache --output type=cacheonly"
        )
        print(
            "  task docker wrapper appends the real suite to the rendered feature Dockerfile"
        )
        print("  test stage runs as vscode in bash -lc with passwd-derived HOME")
        print("  remove only the named score-m6-gates-* buildx builder")
        print(
            "  monitor free disk every 2s and cancel the build process group if "
            f"free space falls below {build_stop_free_gib:g} GiB"
        )
        print(
            "  this is a fresh build plus build-stage test run; it does not load "
            "or launch the published image"
        )


def run_logged(
    args: list[str],
    log_path: Path,
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    monitor_min_free_gib: float | None = None,
    monitor_interval_seconds: float = DEFAULT_DISK_CHECK_INTERVAL,
) -> None:
    print(f"+ {shell_join(args)}", flush=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if monitor_min_free_gib is not None:
        free_gib = shutil.disk_usage(TASK_ROOT).free / GIB
        if free_gib < monitor_min_free_gib:
            raise GateError(
                f"free disk {free_gib:.2f} GiB is below live-build limit "
                f"{monitor_min_free_gib:g} GiB; command not started"
            )
    with log_path.open("ab") as log:
        process = subprocess.Popen(
            args,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        assert process.stdout is not None
        monitor_stop = threading.Event()
        monitor_lock = threading.Lock()
        monitor_triggered: list[str] = []

        def watch_disk() -> None:
            while not monitor_stop.wait(monitor_interval_seconds):
                free_gib = shutil.disk_usage(TASK_ROOT).free / GIB
                if process.poll() is not None:
                    return
                if free_gib >= monitor_min_free_gib:
                    continue
                message = (
                    f"LIVE DISK LIMIT: {free_gib:.2f} GiB free is below "
                    f"{monitor_min_free_gib:g} GiB; cancelling process group "
                    f"for: {shell_join(args)}"
                )
                monitor_triggered.append(message)
                with monitor_lock:
                    log.write((message + "\n").encode())
                    log.flush()
                print(message, file=sys.stderr, flush=True)
                try:
                    os.killpg(process.pid, signal.SIGINT)
                except ProcessLookupError:
                    return
                if not monitor_stop.wait(5):
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        return
                if not monitor_stop.wait(5):
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        return
                return

        monitor_thread = None
        if monitor_min_free_gib is not None:
            monitor_thread = threading.Thread(target=watch_disk, daemon=True)
            monitor_thread.start()
        try:
            for line in iter(process.stdout.readline, b""):
                sys.stdout.buffer.write(line)
                sys.stdout.buffer.flush()
                with monitor_lock:
                    log.write(line)
            return_code = process.wait()
        except KeyboardInterrupt as error:
            try:
                os.killpg(process.pid, signal.SIGINT)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()
            raise GateError(
                f"command interrupted; its process group was terminated; see {log_path}"
            ) from error
        finally:
            monitor_stop.set()
            if monitor_thread is not None:
                monitor_thread.join()
    if monitor_triggered:
        raise GateError(
            f"live disk monitor cancelled command; see {log_path}: "
            f"{monitor_triggered[0]}"
        )
    if return_code:
        raise GateError(f"command failed ({return_code}); see {log_path}")


def ensure_disk_budget(min_free_gib: float) -> None:
    free_gib = shutil.disk_usage(TASK_ROOT).free / GIB
    print(f"Free disk: {free_gib:.2f} GiB")
    if free_gib < min_free_gib:
        raise GateError(
            f"need at least {min_free_gib:g} GiB free before starting; "
            "no Docker operation was started"
        )


def snapshot_source(source: Path, workspace: Path, log_path: Path) -> None:
    if not source.is_dir():
        raise GateError(f"candidate worktree does not exist: {source}")
    workspace.mkdir(parents=True, exist_ok=False)
    # Copy current tracked and untracked source while excluding Git metadata.
    # The temporary repository below gives post-create a safe place for hooks.
    exclusions = (
        "/.git",
        "/.venv",
        "/venv",
        "/bazel-*",
        "/prepared-tools/nix-runtime/***",
        "/src/s-core-devcontainer/.devcontainer/prepared-tools/nix-runtime/***",
        "/native/nix/store/***",
        "/native/nix/activation/***",
        "/native/nix/release-amd64/***",
        "/native/nix/release-arm64/***",
        "/prepared-tools/release-amd64/***",
        "/prepared-tools/release-arm64/***",
        "/experiments/tool-manager-nix/reference/evidence/***",
        "/experiments/tool-manager-nix/reference/out/***",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".cache",
        ".tox",
        ".nox",
        "node_modules",
    )
    command = ["rsync", "-a", "--delete", "--chmod=u+rwX"]
    command.extend(f"--exclude={pattern}" for pattern in exclusions)
    command.extend((f"{source}/", f"{workspace}/"))
    run_logged(command, log_path)
    run_logged(["git", "init", "-q"], log_path, cwd=workspace)


def write_docker_wrapper(
    *,
    path: Path,
    mode: str,
    run_dir: Path,
    docker_path: str,
    builder: str | None = None,
) -> None:
    wrapper = f"""#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

real_docker = {docker_path!r}
run_dir = Path({str(run_dir)!r})
mode = {mode!r}
builder = {builder!r}
args = sys.argv[1:]

def get_tags(values):
    found = []
    index = 2
    while index < len(values):
        value = values[index]
        if value in ("-t", "--tag") and index + 1 < len(values):
            found.append(values[index + 1])
            index += 2
            continue
        if value.startswith("--tag="):
            found.append(value.split("=", 1)[1])
        elif value.startswith("-t="):
            found.append(value.split("=", 1)[1])
        index += 1
    return found

def set_file(values):
    indices = []
    index = 2
    while index < len(values):
        value = values[index]
        if value in ("-f", "--file"):
            if index + 1 >= len(values):
                raise RuntimeError("Docker build file flag has no value")
            indices.append((index + 1, values[index + 1], False))
            index += 2
            continue
        if value.startswith("--file="):
            indices.append((index, value.split("=", 1)[1], True))
        index += 1
    if len(indices) != 1:
        raise RuntimeError(f"expected one generated Dockerfile, found {{len(indices)}}")
    slot, original, inline = indices[0]
    if original == "-":
        raise RuntimeError("cannot append feature tests to a stdin Dockerfile")
    dockerfile = Path(original)
    if not dockerfile.is_absolute():
        dockerfile = (Path.cwd() / dockerfile).resolve()
    if not dockerfile.is_file():
        raise RuntimeError(f"generated Dockerfile not found: {{dockerfile}}")
    destination = run_dir / "rendered-feature-test.Dockerfile"
    contents = dockerfile.read_text()
    if "score-m6-feature-tests" in contents:
        raise RuntimeError("task feature test stage was already appended")
    contents += "\\n\\n# score-m6-feature-tests: existing feature test invocation\\n"
    contents += "COPY --chown=vscode:vscode src/s-core-devcontainer/test-project /tmp/score-m6-test-project\\n"
    contents += "USER vscode\\n"
    contents += '''RUN profile_home="$(getent passwd "$(id -un)" | cut -d: -f6)" && test -n "$profile_home" && HOME="$profile_home" bash -lc 'test "$(id -un)" = vscode && test "$HOME" = "$(getent passwd "$(id -un)" | cut -d: -f6)" && bash /tmp/score-m6-test-project/test.sh'
'''
    destination.write_text(contents)
    os.chmod(destination, 0o600)
    if inline:
        values[slot] = "--file=" + str(destination)
    else:
        values[slot] = str(destination)

def normalize_published(values):
    kept = values[:2]
    index = 2
    while index < len(values):
        value = values[index]
        if value in ("--load", "--push"):
            index += 1
            continue
        if value in ("--output", "-o", "--target"):
            index += 2
            continue
        if value.startswith("--output=") or value.startswith("-o=") or value.startswith("--target="):
            index += 1
            continue
        kept.append(value)
        index += 1
    if not any(item == "--no-cache" for item in kept):
        kept.append("--no-cache")
    if not any(item == "--platform" or item.startswith("--platform=") for item in kept):
        kept.extend(["--platform", "linux/amd64"])
    kept.extend(["--output", "type=cacheonly"])
    return kept

if len(args) >= 2 and args[0:2] == ["buildx", "build"]:
    tags = get_tags(args)
    if mode == "lifecycle":
        for tag in tags:
            check = subprocess.run(
                [real_docker, "image", "inspect", tag],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if check.returncode == 0:
                raise SystemExit(f"refusing to overwrite pre-existing image tag: {{tag}}")
        with (run_dir / "image-tags.jsonl").open("a") as stream:
            for tag in tags:
                stream.write(json.dumps(tag) + "\\n")
    if mode == "published":
        set_file(args)
        args = normalize_published(args)
    if builder:
        if "--builder" not in args:
            args[2:2] = ["--builder", builder]

result = subprocess.run([real_docker, *args], check=False)
raise SystemExit(result.returncode)
"""
    path.write_text(wrapper)
    path.chmod(0o700)


def list_volume_names(docker: str) -> set[str]:
    """Read names only so task mounts can be compared with pre-run state."""
    result = subprocess.run(
        [docker, "volume", "ls", "-q"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        raise GateError(
            f"could not snapshot Docker volume names before lifecycle: "
            f"{result.stderr.strip()}"
        )
    return set(result.stdout.split())


def cleanup_containers(
    docker: str,
    run_id: str,
    workspace: Path,
    preexisting_volumes: set[str] | None,
    run_dir: Path,
    log_path: Path,
) -> bool:
    label = f"score-m6-gates.run={run_id}"
    result = subprocess.run(
        [docker, "ps", "-aq", "--filter", f"label={label}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        print(
            f"warning: could not query task-labeled containers: {result.stderr.strip()}"
        )
        return False
    clean = True
    journal = {
        "run_id": run_id,
        "label": label,
        "workspace": str(workspace),
        "preexisting_volume_names_persisted": False,
        "container_mounts": [],
        "workspace_owner_restore": [],
    }
    journal_path = run_dir / "volume-journal.json"
    journal_path.write_text(json.dumps(journal, indent=2) + "\n")
    newly_created: set[str] = set()
    for container_id in result.stdout.split():
        inspected = subprocess.run(
            [docker, "inspect", "--format", "{{json .Mounts}}", container_id],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if inspected.returncode:
            print(
                f"warning: could not inspect task container mounts {container_id}: "
                f"{inspected.stderr.strip()}"
            )
            clean = False
            mounts = []
        else:
            try:
                mounts = json.loads(inspected.stdout)
                if not isinstance(mounts, list):
                    raise ValueError("Docker mount output is not a list")
            except json.JSONDecodeError as error:
                print(
                    f"warning: malformed mount data for task container {container_id}: {error}"
                )
                clean = False
                mounts = []
            except ValueError as error:
                print(
                    f"warning: malformed mount data for task container {container_id}: {error}"
                )
                clean = False
                mounts = []
        for mount in mounts:
            if mount.get("Type") != "volume" or not mount.get("Name"):
                continue
            name = mount["Name"]
            preexisting = preexisting_volumes is None or name in preexisting_volumes
            record = {
                "container_id": container_id,
                "name": name,
                "destination": mount.get("Destination"),
                "preexisting": preexisting,
                "cleanup": "preserve-preexisting" if preexisting else "pending-remove",
            }
            journal["container_mounts"].append(record)
            if not preexisting:
                newly_created.add(name)
        journal_path.write_text(json.dumps(journal, indent=2) + "\n")
        remote_workspace = f"/workspaces/{workspace.name}"
        owner_restore = subprocess.run(
            [
                docker,
                "exec",
                "--user",
                "0",
                container_id,
                "find",
                remote_workspace,
                "-xdev",
                "-uid",
                "0",
                "-exec",
                "chown",
                f"{os.getuid()}:{os.getgid()}",
                "{}",
                "+",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        owner_status = (
            "restored-to-host-owner"
            if owner_restore.returncode == 0
            else "restore-failed"
        )
        journal["workspace_owner_restore"].append(
            {
                "container_id": container_id,
                "container_path": remote_workspace,
                "host_uid": os.getuid(),
                "host_gid": os.getgid(),
                "status": owner_status,
                "error": owner_restore.stderr.strip()
                if owner_restore.returncode
                else None,
            }
        )
        journal_path.write_text(json.dumps(journal, indent=2) + "\n")
        if owner_restore.returncode:
            print(
                f"warning: could not restore task workspace ownership in container "
                f"{container_id}: {owner_restore.stderr.strip()}"
            )
            clean = False
        try:
            run_logged([docker, "rm", "-f", container_id], log_path)
        except GateError as error:
            print(f"warning: task container cleanup failed: {error}")
            clean = False
    journal_path = run_dir / "volume-journal.json"
    for name in sorted(newly_created):
        in_use = subprocess.run(
            [docker, "ps", "-aq", "--filter", f"volume={name}"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if in_use.returncode:
            print(
                f"warning: could not check task volume use for {name}: {in_use.stderr.strip()}"
            )
            clean = False
            status = "not-removed-use-check-failed"
        elif in_use.stdout.strip():
            print(
                f"preserving newly-created task mount volume still used by a container: {name}"
            )
            clean = False
            status = "preserved-in-use"
        else:
            try:
                run_logged([docker, "volume", "rm", name], log_path)
                status = "removed"
            except GateError as error:
                print(f"warning: task volume cleanup failed for {name}: {error}")
                clean = False
                status = "remove-failed"
        for record in journal["container_mounts"]:
            if record["name"] == name:
                record["cleanup"] = status
        journal_path.write_text(json.dumps(journal, indent=2) + "\n")
    return clean


def task_container_ids(docker: str, run_id: str) -> list[str]:
    label = f"score-m6-gates.run={run_id}"
    result = subprocess.run(
        [docker, "ps", "-aq", "--filter", f"label={label}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        raise GateError(
            f"could not query the task container label {label}: {result.stderr.strip()}"
        )
    return result.stdout.split()


def run_later_terminal_check(
    devcontainer: Path,
    docker: str,
    workspace: Path,
    container_id: str,
    run_dir: Path,
    log_path: Path,
    min_free_gib: float,
    disk_check_interval: float,
) -> None:
    command = "\n".join(
        (
            "set +e; set -u",
            "result=0",
            'printf \'interactive-shell user=%s home=%s cwd=%s\\n\' "$(id -un)" "$HOME" "$PWD"',
            "for tool in uv uvx ruff pre-commit; do",
            '    path=$(type -P "$tool" 2>/dev/null)',
            '    if [[ -n "$path" ]]; then',
            '        resolved=$(readlink -f "$path")',
            "        owner=$(stat -c '%U:%G' \"$resolved\" 2>/dev/null)",
            '        printf \'tool=%s path=%s resolved=%s owner=%s\\n\' "$tool" "$path" "$resolved" "$owner"',
            '        if ! "$tool" --version; then result=1; fi',
            "    else",
            "        printf 'tool=%s missing-from-PATH\\n' \"$tool\"",
            "        result=1",
            "    fi",
            "done",
            "if [[ -f .git/hooks/pre-commit ]]; then",
            "    printf 'pre-commit-hook=%s owner=%s\\n' \"$(readlink -f .git/hooks/pre-commit)\" \"$(stat -c '%U:%G' .git/hooks/pre-commit)\"",
            "else",
            "    printf 'pre-commit-hook=missing\\n'",
            "    result=1",
            "fi",
            f"if server=$({shell_quote(docker)} info --format '{{{{.ServerVersion}}}}'); then printf 'dind-server=%s\\n' \"$server\"; else result=1; fi",
            f"if {shell_quote(docker)} buildx inspect --bootstrap; then :; else result=1; fi",
            "exit $result",
        )
    )
    run_logged(
        [
            str(devcontainer),
            "exec",
            "--workspace-folder",
            str(workspace),
            "--container-id",
            container_id,
            "--user-data-folder",
            str(run_dir / "user-data"),
            "bash",
            "-ic",
            command,
        ],
        log_path,
        monitor_min_free_gib=min_free_gib,
        monitor_interval_seconds=disk_check_interval,
    )


def cleanup_lifecycle_images(docker: str, run_dir: Path, log_path: Path) -> bool:
    tag_file = run_dir / "image-tags.jsonl"
    if not tag_file.exists():
        print(
            "warning: no task image tags were recorded; leaving daemon images untouched"
        )
        return False
    tags = []
    for line in tag_file.read_text().splitlines():
        try:
            tags.append(json.loads(line))
        except json.JSONDecodeError:
            print("warning: malformed task image tag record; skipping that record")
    if not tags:
        print(
            "warning: task image tag record is empty; leaving daemon images untouched"
        )
        return False
    clean = True
    for tag in dict.fromkeys(tags):
        exists = subprocess.run(
            [docker, "image", "inspect", tag],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if exists.returncode == 0:
            try:
                run_logged([docker, "image", "rm", tag], log_path)
            except GateError as error:
                print(f"warning: task image cleanup failed for {tag}: {error}")
                clean = False
    return clean


def cleanup_builder(docker: str, builder: str, log_path: Path) -> bool:
    # The builder is unique to this run and was created without selecting it
    # globally. Buildx removes its own named container/cache with this command.
    result = subprocess.run(
        [docker, "buildx", "rm", builder],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    with log_path.open("a") as log:
        log.write(result.stdout or "")
    if result.returncode:
        print(
            f"warning: could not remove task builder {builder}: "
            f"{(result.stdout or '').strip()}"
        )
        return False
    return True


def write_nix_devcontainer_shim(path: Path, cli: Path, docker_wrapper: Path) -> None:
    shim = f"""#!/usr/bin/env python3
import os
import sys

real_cli = {str(cli)!r}
docker_wrapper = {str(docker_wrapper)!r}
args = sys.argv[1:]
if not args or args[0] != "build":
    os.execv(real_cli, [real_cli, *args])

# The Nix build script normally adds the shared registry cache. A gate build is
# fresh and cache-only, so remove that input and force the task-owned CLI options.
filtered = []
index = 0
while index < len(args):
    value = args[index]
    if value == "--cache-from":
        index += 2
        continue
    if value.startswith("--cache-from=") or value in ("--push",):
        index += 1
        continue
    filtered.append(value)
    index += 1
filtered.extend([
    "--no-cache",
    "--output", "type=cacheonly",
    "--docker-path", docker_wrapper,
])
os.execv(real_cli, [real_cli, *filtered])
"""
    path.write_text(shim)
    path.chmod(0o700)


def execute_nix_published_build(
    source: Path,
    run_dir: Path,
    run_id: str,
    docker_wrapper: Path,
    log_path: Path,
    *,
    build_stop_free_gib: float,
    disk_check_interval: float,
) -> None:
    if not NIX_RELEASE.is_dir():
        raise GateError(f"retained M5 Nix release is missing: {NIX_RELEASE}")
    build_script = source / "scripts/build.sh"
    if not build_script.is_file():
        raise GateError(f"Nix build entrypoint not found: {build_script}")
    cli_bin = run_dir / "cli-bin"
    cli_bin.mkdir(parents=True, exist_ok=True)
    shim = cli_bin / "devcontainer"
    write_nix_devcontainer_shim(shim, DEFAULT_DEVCONTAINER, docker_wrapper)
    build_tmp = run_dir / "build-tmp"
    build_tmp.mkdir(parents=True, exist_ok=True)

    build_env = os.environ.copy()
    build_env["PATH"] = f"{cli_bin}{os.pathsep}{build_env.get('PATH', '')}"
    build_env["TMPDIR"] = str(build_tmp)
    build_env["PYTHONDONTWRITEBYTECODE"] = "1"
    build_env["SCORE_M5_NIX_ARTIFACTS"] = str(NIX_ARTIFACTS_ROOT)
    build_env["SCORE_NIX_PREPARED_RELEASE"] = str(NIX_RELEASE)
    build_env["SCORE_NIX_KEEP_BUILD_CONTEXT"] = "0"
    build_env["SCORE_NIX_PUSH"] = "0"
    build_env["SCORE_NIX_IMAGE_REPOSITORY"] = "score-m6-gates-nix"
    run_logged(
        ["bash", str(build_script), "--amd64", f"score-m6-nix-{run_id}"],
        log_path,
        cwd=source,
        env=build_env,
        monitor_min_free_gib=build_stop_free_gib,
        monitor_interval_seconds=disk_check_interval,
    )


def execute_lifecycle(
    candidate: str,
    source: Path,
    *,
    devcontainer: Path,
    min_free_gib: float,
    keep_workspace: bool,
) -> None:
    run_id = new_run_id(candidate, "lifecycle")
    run_dir = TASK_ROOT / run_id
    workspace = run_dir / f"workspace-score-m6-{candidate}-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)
    log_path = run_dir / "lifecycle.log"
    docker = shutil.which("docker")
    if not docker:
        raise GateError("docker executable not found")
    if not devcontainer.is_file():
        raise GateError(f"Dev Containers CLI not found: {devcontainer}")

    ensure_disk_budget(min_free_gib)
    success = False
    failure: GateError | None = None
    preexisting_volumes: set[str] | None = None
    terminal_attempted = False
    terminal_passed = False
    try:
        snapshot_source(source, workspace, log_path)
        ensure_disk_budget(min_free_gib)
        preexisting_volumes = list_volume_names(docker)
        (run_dir / "volume-baseline.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "label": f"score-m6-gates.run={run_id}",
                    "preexisting_volume_count": len(preexisting_volumes),
                    "volume_names_persisted": False,
                },
                indent=2,
            )
            + "\n"
        )
        wrapper = run_dir / "docker-wrapper.py"
        write_docker_wrapper(
            path=wrapper,
            mode="lifecycle",
            run_dir=run_dir,
            docker_path=docker,
        )
        # This uses the normal Docker build selection without changing it. The
        # only host mount is the disposable workspace copy with its task-local .git.
        run_logged(
            [
                str(devcontainer),
                "up",
                "--workspace-folder",
                str(workspace),
                "--id-label",
                f"score-m6-gates.run={run_id}",
                "--user-data-folder",
                str(run_dir / "user-data"),
                "--remove-existing-container",
                "--docker-path",
                str(wrapper),
            ],
            log_path,
            monitor_min_free_gib=min_free_gib,
            monitor_interval_seconds=DEFAULT_DISK_CHECK_INTERVAL,
        )
        containers = task_container_ids(docker, run_id)
        if len(containers) != 1:
            raise GateError(
                f"expected one task container with label score-m6-gates.run={run_id}; "
                f"found {len(containers)}"
            )
        terminal_attempted = True
        run_later_terminal_check(
            devcontainer,
            docker,
            workspace,
            containers[0],
            run_dir,
            log_path,
            min_free_gib,
            DEFAULT_DISK_CHECK_INTERVAL,
        )
        terminal_passed = True
        success = True
    except GateError as error:
        failure = error
    finally:
        containers_clean = cleanup_containers(
            docker,
            run_id,
            workspace,
            preexisting_volumes,
            run_dir,
            log_path,
        )
        images_clean = cleanup_lifecycle_images(docker, run_dir, log_path)
        workspace_clean = True
        if not keep_workspace:
            try:
                shutil.rmtree(workspace)
            except FileNotFoundError:
                pass
            except OSError as error:
                print(f"warning: task workspace cleanup failed: {error}")
                workspace_clean = False
            workspace_clean = workspace_clean and not workspace.exists()
    if not containers_clean or not images_clean or not workspace_clean:
        success = False
        cleanup_failure = GateError(
            "task container, image, or workspace cleanup was incomplete; inspect the exact "
            f"task labels/tags and log at {log_path}"
        )
        failure = failure or cleanup_failure
    result_path = run_dir / "result.json"
    result_path.write_text(
        json.dumps(
            {
                "candidate": candidate,
                "gate": "root-generic-node-lifecycle",
                "status": "passed" if success else "failed",
                "source": str(source),
                "workspace_retained": keep_workspace or not workspace_clean,
                "interactive_terminal_check": (
                    "passed"
                    if terminal_passed
                    else "failed"
                    if terminal_attempted
                    else "not-reached"
                ),
                "volume_journal": str(run_dir / "volume-journal.json"),
                "log": str(log_path),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Lifecycle {'passed' if success else 'failed'}; log: {log_path}")
    append_progress(
        f"{candidate} generic Node lifecycle: {'PASSED' if success else 'FAILED'}; "
        f"later interactive-terminal check={'passed' if terminal_passed else 'failed' if terminal_attempted else 'not reached'}; "
        f"volume journal={run_dir / 'volume-journal.json'}; log={log_path}; "
        f"failure={failure or 'none'}"
    )
    if failure:
        raise failure


def execute_published(
    candidate: str,
    source: Path,
    *,
    devcontainer: Path,
    min_free_gib: float,
    build_stop_free_gib: float,
    disk_check_interval: float,
    keep_workspace: bool,
) -> None:
    run_id = new_run_id(candidate, "published")
    run_dir = TASK_ROOT / run_id
    workspace = run_dir / f"workspace-score-m6-{candidate}-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)
    log_path = run_dir / "published-build.log"
    docker = shutil.which("docker")
    if not docker:
        raise GateError("docker executable not found")
    if not devcontainer.is_file():
        raise GateError(f"Dev Containers CLI not found: {devcontainer}")

    ensure_disk_budget(min_free_gib)
    builder = f"score-m6-gates-{candidate}-{uuid.uuid4().hex[:8]}"
    builder_created = False
    success = False
    failure: GateError | None = None
    try:
        if candidate == "nix":
            if not source.is_dir():
                raise GateError(f"candidate worktree does not exist: {source}")
        else:
            snapshot_source(source, workspace, log_path)
        ensure_disk_budget(min_free_gib)

        builder_created = True
        run_logged(
            [
                docker,
                "buildx",
                "create",
                "--name",
                builder,
                "--driver",
                "docker-container",
            ],
            log_path,
        )
        wrapper = run_dir / "docker-wrapper.py"
        write_docker_wrapper(
            path=wrapper,
            mode="published",
            run_dir=run_dir,
            docker_path=docker,
            builder=builder,
        )
        if candidate == "nix":
            execute_nix_published_build(
                source,
                run_dir,
                run_id,
                wrapper,
                log_path,
                build_stop_free_gib=build_stop_free_gib,
                disk_check_interval=disk_check_interval,
            )
        else:
            image_name = published_image_name(candidate, run_id)
            run_logged(
                [
                    str(devcontainer),
                    "build",
                    "--workspace-folder",
                    str(workspace / "src/s-core-devcontainer"),
                    "--image-name",
                    image_name,
                    "--platform",
                    "linux/amd64",
                    "--no-cache",
                    "--output",
                    "type=cacheonly",
                    "--docker-path",
                    str(wrapper),
                ],
                log_path,
                monitor_min_free_gib=build_stop_free_gib,
                monitor_interval_seconds=disk_check_interval,
            )
        success = True
    except GateError as error:
        failure = error
    finally:
        builder_clean = True
        if builder_created:
            builder_clean = cleanup_builder(docker, builder, log_path)
        if not keep_workspace:
            shutil.rmtree(workspace, ignore_errors=True)
    if not builder_clean:
        success = False
        failure = failure or GateError(
            f"could not remove task builder {builder}; inspect {log_path}"
        )
    result_path = run_dir / "result.json"
    result_path.write_text(
        json.dumps(
            {
                "candidate": candidate,
                "gate": "fresh-published-amd64-build-and-feature-tests",
                "status": "passed" if success else "failed",
                "source": str(source),
                "output": "type=cacheonly; no image loaded or launched",
                "source_strategy": (
                    "Nix build.sh stages one task context from stable source"
                    if candidate == "nix"
                    else "task-local source snapshot"
                ),
                "workspace_retained": keep_workspace and candidate != "nix",
                "log": str(log_path),
                "builder": builder,
                "builder_removed": builder_clean if builder_created else False,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Published gate {'passed' if success else 'failed'}; log: {log_path}")
    append_progress(
        f"{candidate} fresh published amd64 build plus appended feature tests: "
        f"{'PASSED' if success else 'FAILED'}; output=type=cacheonly (not loaded/launched); "
        f"builder={builder}; builder_removed={builder_clean if builder_created else False}; "
        f"result={result_path}; log={log_path}; failure={failure or 'none'}"
    )
    if failure:
        raise failure


def execute_candidate(
    candidate: str,
    source: Path,
    *,
    gate: str,
    devcontainer: Path,
    min_free_gib: float,
    build_stop_free_gib: float,
    disk_check_interval: float,
    keep_workspace: bool,
) -> None:
    readiness = candidate_readiness(candidate, gate)
    if not candidate_ready(candidate, gate):
        message = (
            f"{candidate} is pending; readiness file is absent or empty: {readiness}"
        )
        append_progress(message)
        raise GateError(message)
    failures = []
    if gate in ("all", "lifecycle"):
        try:
            execute_lifecycle(
                candidate,
                source,
                devcontainer=devcontainer,
                min_free_gib=min_free_gib,
                keep_workspace=keep_workspace,
            )
        except GateError as error:
            failures.append(f"lifecycle: {error}")
    if gate in ("all", "published"):
        try:
            execute_published(
                candidate,
                source,
                devcontainer=devcontainer,
                min_free_gib=min_free_gib,
                build_stop_free_gib=build_stop_free_gib,
                disk_check_interval=disk_check_interval,
                keep_workspace=keep_workspace,
            )
        except GateError as error:
            failures.append(f"published: {error}")
    if failures:
        raise GateError("; ".join(failures))


def main() -> int:
    args = parse_args()
    TASK_ROOT.mkdir(parents=True, exist_ok=True)
    if args.command == "run":
        source = candidate_source(args.candidate, args.source)
        if args.dry_run:
            print_plan(
                args.candidate,
                source,
                args.gate,
                args.min_free_gib,
                args.build_stop_free_gib,
                args.disk_check_interval,
            )
            return 0
        execute_candidate(
            args.candidate,
            source,
            gate=args.gate,
            devcontainer=DEFAULT_DEVCONTAINER,
            min_free_gib=args.min_free_gib,
            build_stop_free_gib=args.build_stop_free_gib,
            disk_check_interval=args.disk_check_interval,
            keep_workspace=args.keep_workspace,
        )
        return 0

    if args.dry_run:
        for candidate in CANDIDATES:
            if candidate != CANDIDATES[0]:
                print("\n" + "=" * 72 + "\n")
            print_plan(
                candidate,
                candidate_source(candidate),
                args.gate,
                args.min_free_gib,
                args.build_stop_free_gib,
                args.disk_check_interval,
            )
        return 0

    failures = []
    for candidate in CANDIDATES:
        print(f"\n### M6 gates: {candidate} ###", flush=True)
        try:
            execute_candidate(
                candidate,
                candidate_source(candidate),
                gate=args.gate,
                devcontainer=DEFAULT_DEVCONTAINER,
                min_free_gib=args.min_free_gib,
                build_stop_free_gib=args.build_stop_free_gib,
                disk_check_interval=args.disk_check_interval,
                keep_workspace=args.keep_workspace,
            )
        except GateError as error:
            print(f"{candidate} gate failed: {error}", file=sys.stderr)
            failures.append((candidate, str(error)))
    if failures:
        print("\nFailed gates:")
        for candidate, message in failures:
            print(f"- {candidate}: {message}")
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateError as error:
        print(f"gate error: {error}", file=sys.stderr)
        raise SystemExit(1)
