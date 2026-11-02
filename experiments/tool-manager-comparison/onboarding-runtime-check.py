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
"""Exercise added tools without installing a manager or prescribing its layout.

--expected is generated from the candidate's current owners and contains
{"versions": {"starpls": "...", "codespell": "..."}, "bazel_version": "..."}.
Derive bazel_version from the existing provider policy. Run with the prepared
published commands on PATH, or supply their absolute paths. This checks tool
behavior; image, user and network acceptance belong to the outer invocation.
"""

import argparse
import json
import os
import re
import selectors
import subprocess
import tempfile
import time
from pathlib import Path


def exchange(server, expected_version, bazel_version, directory, records):
    """Exercise the protocol; this does not test project indexing or diagnostics."""
    # Starpls starts background Bazel discovery even for an empty client. Give
    # it a recognized workspace and the existing provider pin, so this check
    # cannot accidentally select/download the latest Bazel release.
    (directory / "MODULE.bazel").touch()
    (directory / ".bazelversion").write_text(bazel_version + "\n")
    (directory / ".bazelrc").write_text("startup --batch\n")
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(
            [server, "server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=errors,
            cwd=directory,
            env={**os.environ, "USE_BAZEL_VERSION": bazel_version},
        )
        buffer = bytearray()

        def send(message):
            body = json.dumps(message).encode()
            process.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
            process.stdin.flush()

        def response(identifier):
            deadline = time.monotonic() + 20
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while time.monotonic() < deadline:
                    separator = buffer.find(b"\r\n\r\n")
                    if separator != -1:
                        header = bytes(buffer[:separator]).decode("ascii")
                        fields = dict(
                            line.lower().split(":", 1) for line in header.split("\r\n")
                        )
                        length = int(fields["content-length"])
                        if not 0 <= length <= 4 * 1024 * 1024:
                            raise AssertionError("Invalid LSP response length")
                        end = separator + 4 + length
                        if len(buffer) >= end:
                            message = json.loads(bytes(buffer[separator + 4 : end]))
                            del buffer[:end]
                            if message.get("id") == identifier:
                                if "error" in message:
                                    raise AssertionError(message)
                                return message
                            continue
                    if not selector.select(max(0, deadline - time.monotonic())):
                        break
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise AssertionError("starpls exited before the LSP response")
                    buffer.extend(chunk)
            raise AssertionError(f"Timed out waiting for LSP response {identifier}")

        try:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"processId": None, "rootUri": None, "capabilities": {}},
                }
            )
            initialized = response(1)
            assert isinstance(initialized.get("result", {}).get("capabilities"), dict)
            send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
            send({"jsonrpc": "2.0", "id": 2, "method": "shutdown", "params": None})
            stopped = response(2)
            assert "result" in stopped
            send({"jsonrpc": "2.0", "method": "exit"})
            status = process.wait(timeout=5)
            assert status == 0, status
            records["starpls_lsp"] = {
                "version": expected_version,
                "scope": "initialize/shutdown protocol; no project-analysis assertion",
                "initialize": initialized,
                "shutdown": stopped,
                "exit": status,
            }
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdin.close()
            process.stdout.close()
            errors.seek(0)
            records["starpls_stderr"] = errors.read().decode(errors="replace")[-4000:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--starpls", default="starpls")
    parser.add_argument("--codespell", default="codespell")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    policy = json.loads(args.expected.read_text())
    expected = policy["versions"]
    records = {"versions": expected, "uid": os.getuid(), "commands": []}

    def run(command):
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=30, check=False
        )
        record = {
            "argv": command,
            "exit": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
        records["commands"].append(record)
        return completed.returncode, completed.stdout + completed.stderr

    try:
        for name, executable in (
            ("starpls", args.starpls),
            ("codespell", args.codespell),
        ):
            flag = "version" if name == "starpls" else "--version"
            status, observed = run([executable, flag])
            assert status == 0, observed
            pattern = r"(?<![\d.])" + re.escape(expected[name]) + r"(?![\d.])"
            assert re.search(pattern, observed), (name, expected[name], observed)
        with tempfile.TemporaryDirectory(prefix="score-onboarding-") as temporary:
            directory = Path(temporary)
            exchange(
                args.starpls,
                expected["starpls"],
                policy["bazel_version"],
                directory,
                records,
            )
            clean = directory / "clean.txt"
            clean.write_text("This sentence contains a word.\n")
            status, observed = run([args.codespell, str(clean)])
            assert status == 0, observed
            typo = directory / "typo.txt"
            typo.write_text("This sentence contains teh typo.\n")
            status, observed = run([args.codespell, str(typo)])
            assert status != 0 and "teh ==> the" in observed, observed
        records["result"] = "passed"
    except Exception as error:
        records["result"] = "failed"
        records["error"] = str(error)
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps({"result": "passed", "versions": expected, "uid": os.getuid()}))


if __name__ == "__main__":
    main()
