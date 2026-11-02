#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Compare actual direct and strict prepared calls; suitable for offline containers."""

import argparse
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_tools.catalog import load_catalog_versions


def language_server(command, workspace, environment, messages):
    process = subprocess.Popen(
        command,
        cwd=workspace,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    responses = []
    pending = b""
    deadline = time.monotonic() + 30

    def send(message):
        body = json.dumps(message).encode()
        process.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
        process.stdin.flush()

    def receive(identity):
        nonlocal pending
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                while b"\r\n\r\n" in pending:
                    header, body = pending.split(b"\r\n\r\n", 1)
                    length = next(
                        int(line.split(b":", 1)[1])
                        for line in header.split(b"\r\n")
                        if line.lower().startswith(b"content-length:")
                    )
                    if len(body) < length:
                        break
                    response = json.loads(body[:length])
                    pending = body[length:]
                    responses.append(response)
                    if response.get("id") == identity:
                        if "result" not in response:
                            raise RuntimeError(f"LSP request failed: {response}")
                        return
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise TimeoutError(f"LSP response timed out: {command}")
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError(
                        f"LSP exited before response {identity}: {command}"
                    )
                pending += chunk

    try:
        send(messages[0])
        receive(1)
        send(messages[1])
        send(messages[2])
        receive(2)
        send(messages[3])
        process.stdin.close()
        status = process.wait(timeout=5)
        errors = process.stderr.read().decode()
        if status:
            raise RuntimeError(f"LSP exit {status}: {command}: {errors}")
        return {
            "argv": command,
            "exit": status,
            "response_ids": [
                response["id"] for response in responses if "id" in response
            ],
        }
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    versions = load_catalog_versions()
    workspace = args.output.parent / "prepared-fixtures"
    workspace.mkdir()
    poison = workspace / "poison"
    poison.mkdir()
    marker = workspace / "intercepted"
    for name in ("bazel", "mise", "aqua", "nix", "uv", "uvx"):
        command = poison / name
        command.write_text(
            f'#!/bin/sh\nprintf "%s\\n" "{name}" "$@" "${{SCORE_SMOKE_PHASE:-unknown}}" >> "{marker}"\nexit 97\n'
        )
        command.chmod(0o755)
    (workspace / "bad input.py").write_text("import os\n")
    (workspace / "bad input.sh").write_text("#!/bin/sh\necho $value\n")
    (workspace / ".pre-commit-config.yaml").write_text("repos: []\n")
    environment = {
        **os.environ,
        "PATH": str(poison) + ":/usr/bin:/bin",
        "RUN_TOOL_CONTAINER_MODE": "host",
        "SCORE_TOOLS_PREFIX": str(args.prefix),
        "UV_OFFLINE": "1",
    }
    runner = Path(__file__).resolve().parents[1] / "run-tool"
    cases = [
        ("uv", ["--version"], 0, "uv "),
        ("uvx", ["--version"], 0, "uvx "),
        ("ruff", ["--version"], 0, "ruff "),
        ("pre-commit", ["--version"], 0, "pre-commit "),
        ("ruff", ["check", "bad input.py"], 1, "F401"),
        ("shellcheck", ["bad input.sh"], 1, "SC2086"),
        ("starpls", ["version"], 0, "starpls"),
        ("buildifier", ["--version"], 0, "buildifier"),
        ("pre-commit", ["validate-config", ".pre-commit-config.yaml"], 0, ""),
        ("actionlint", ["--version"], 0, ""),
        ("yamlfmt", ["--version"], 0, ""),
        ("apm", ["--version"], 0, ""),
        ("opencode", ["--version"], 0, ""),
        ("basedpyright", ["--version"], 0, ""),
        ("pytest", ["--version"], 0, ""),
        ("py.test", ["--version"], 0, ""),
    ]
    records = []
    for name, arguments, expected, text in cases:
        results = []
        commands = [
            [str(args.prefix / "bin" / name), *arguments],
            ["/bin/bash", str(runner), "--strict", name, *arguments],
        ]
        for command in commands:
            environment["SCORE_SMOKE_PHASE"] = "prepared:" + name
            run = subprocess.run(
                command, cwd=workspace, env=environment, text=True, capture_output=True
            )
            results.append(
                {
                    "argv": command,
                    "exit": run.returncode,
                    "stdout": run.stdout,
                    "stderr": run.stderr,
                }
            )
        if (
            results[0]["exit"] != expected
            or text not in results[0]["stdout"] + results[0]["stderr"]
        ):
            raise RuntimeError(f"Unexpected real {name} behavior: {results}")
        if arguments == ["--version"] or name == "starpls":
            version = versions["pytest" if name == "py.test" else name]
            if not re.search(
                r"(?<![0-9.])" + re.escape(version) + r"(?![0-9.])",
                results[0]["stdout"] + results[0]["stderr"],
            ):
                raise RuntimeError(f"Unexpected owner version for {name}: {results}")
        if any(
            results[0][key] != results[1][key] for key in ("exit", "stdout", "stderr")
        ):
            raise RuntimeError(f"Direct/strict results differ: {results}")
        records.append({"tool": name, "results": results})
    (workspace / "good.py").write_text("value: int = 1\n")
    (workspace / "test_sample.py").write_text(
        "def test_example():\n    assert 2 + 2 == 4\n"
    )
    for name, arguments in (
        ("basedpyright", ["good.py"]),
        ("pytest", ["-q", "test_sample.py"]),
    ):
        command = [str(args.prefix / "bin" / name), *arguments]
        environment["SCORE_SMOKE_PHASE"] = "behavior:" + name
        run = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if run.returncode:
            raise RuntimeError(
                f"Prepared behavior failed: {command}: {run.stdout} {run.stderr}"
            )
        records.append(
            {
                "tool": name,
                "behavior": {
                    "argv": command,
                    "exit": run.returncode,
                    "stdout": run.stdout,
                    "stderr": run.stderr,
                },
            }
        )
    lsp_records = []
    if marker.exists():
        raise RuntimeError(
            "Prepared invocation intercepted a resolver: " + marker.read_text()
        )
    lsp_environment = {
        **environment,
        "PATH": str(args.prefix / "bin") + ":/usr/local/bin:/usr/bin:/bin",
        "USE_BAZEL_FALLBACK_VERSION": "error:score-own-no-engine",
    }
    lsp_environment.pop("USE_BAZEL_VERSION", None)
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "processId": None,
                "rootUri": workspace.as_uri(),
                "capabilities": {},
            },
        },
        {"jsonrpc": "2.0", "method": "initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "shutdown", "params": None},
        {"jsonrpc": "2.0", "method": "exit", "params": None},
    ]
    for name, arguments in (
        ("basedpyright-langserver", ["--stdio"]),
        ("starpls", ["server"]),
        ("ruff", ["server"]),
    ):
        command = [str(args.prefix / "bin" / name), *arguments]
        environment["SCORE_SMOKE_PHASE"] = "lsp:" + name
        lsp_records.append(
            {
                "tool": name,
                **language_server(command, workspace, lsp_environment, messages),
            }
        )
    guard_environment = {
        **environment,
        "USE_BAZEL_FALLBACK_VERSION": "error:score-own-no-engine",
    }
    guard_environment.pop("USE_BAZEL_VERSION", None)
    guard = subprocess.run(
        [str(args.prefix / "bin/bazelisk"), "version"],
        cwd=workspace,
        env=guard_environment,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if (
        guard.returncode != 1
        or "score-own-no-engine" not in guard.stdout + guard.stderr
    ):
        raise RuntimeError(f"Unexpected guarded Bazelisk behavior: {guard}")
    if marker.exists():
        raise RuntimeError(
            "Prepared calls intercepted a manager/resolver/Bazel: " + marker.read_text()
        )
    args.output.write_text(
        json.dumps(
            {
                "status": "passed",
                "uid": os.getuid(),
                "cwd": str(workspace),
                "intercepted": False,
                "cases": records,
                "language_servers": lsp_records,
                "bazelisk_guard": {
                    "exit": guard.returncode,
                    "stdout": guard.stdout,
                    "stderr": guard.stderr,
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(args.output)


if __name__ == "__main__":
    main()
