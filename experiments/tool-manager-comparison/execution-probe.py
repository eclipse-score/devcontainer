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
"""Audit direct prepared commands inside the isolated comparison runtime.

This script observes one native and one Python CLI, not a general release runner.
Run via run-execution-probes.py; payloads stay read-only and managers are absent.
"""

import argparse
import json
import os
import re
import signal
import statistics
import subprocess
import time
from pathlib import Path


def interpreter(script):
    first = script.read_text().splitlines()[0]
    assert first.startswith("#!/"), first
    return first[2:].strip()


def python_reference(entry):
    """Bypass only this known shell wrapper, preserving its runtime environment."""
    source = entry.read_text()
    environment = os.environ.copy()
    if "exec -a" in source:
        match = re.search(r'exec -a "\$0" "([^"]+)"', source)
        assert match, source
        wrapped = Path(match[1])
        python = interpreter(wrapped)
        assert " " not in python, python
        environment["PATH"] = os.pathsep.join(
            [str(Path(python).parent), str(entry.parent), environment["PATH"]]
        )
        assert "export PYTHONNOUSERSITE='true'" in source
        environment["PYTHONNOUSERSITE"] = "true"
        return [python, str(wrapped)], environment
    python = interpreter(entry)
    assert " " not in python, python
    return [python, str(entry)], environment


def summarize(samples):
    ordered = sorted(samples)
    return {
        "median_ms": statistics.median(samples),
        "min_ms": ordered[0],
        "p10_ms": ordered[int((len(ordered) - 1) * 0.1)],
        "p90_ms": ordered[int((len(ordered) - 1) * 0.9)],
        "max_ms": ordered[-1],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--starpls", type=Path, required=True)
    parser.add_argument("--codespell", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=40)
    args = parser.parse_args()
    assert args.samples >= 10
    output = args.output
    output.mkdir(exist_ok=True)
    native = args.starpls.resolve(strict=True)
    python_entry = args.codespell.resolve(strict=True)
    reference, reference_env = python_reference(python_entry)
    report = {
        "candidate": args.candidate,
        "uid": os.getuid(),
        "scope": "Prepared Linux amd64 native/Python entrypoints; no cold-install or all-tool claim",
        "environment": {key: os.environ[key] for key in ("HOME", "PATH")},
        "mounts": [
            line
            for line in Path("/proc/mounts").read_text().splitlines()
            if line.split()[1] in ("/", "/opt/score-tools", "/nix/store")
        ],
        "commands": [],
        "traces": {},
        "timings": {},
        "signals": [],
    }
    assert report["uid"] != 0
    assert all("ro" in row.split()[3].split(",") for row in report["mounts"])

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(command, env=None, expected=0):
        result = subprocess.run(
            list(map(str, command)), env=env, text=True, capture_output=True, timeout=15
        )
        report["commands"].append(
            {
                "argv": list(map(str, command)),
                "exit": result.returncode,
                "stdout": result.stdout[-1500:],
                "stderr": result.stderr[-1500:],
            }
        )
        save()
        assert result.returncode == expected, report["commands"][-1]
        return result

    report["versions"] = {
        "starpls": run([args.starpls, "version"]).stdout.strip(),
        "codespell": run([args.codespell, "--version"]).stdout.strip(),
        "strace": run(["strace", "--version"]).stdout.splitlines()[0],
    }
    assert "0.1.22" in report["versions"]["starpls"]
    report["entrypoints"] = {
        "native_exposed": str(args.starpls),
        "native_resolved": str(native),
        "python_exposed": str(args.codespell),
        "python_resolved": str(python_entry),
        "python_source": python_entry.read_text(),
        "python_reference": reference,
        "reference_environment_overrides": {
            key: value
            for key, value in reference_env.items()
            if os.environ.get(key) != value
        },
    }
    clean = Path.cwd() / "clean.txt"
    typo = Path.cwd() / "typo.txt"
    assert (
        clean.read_text() == "the tool works\n"
        and typo.read_text() == "teh tool works\n"
    )

    def trace(name, command, *, env=None, expected=0):
        raw = output / (name + ".trace")
        run(
            [
                "strace",
                "-f",
                "-qq",
                "-s",
                "512",
                "-o",
                raw,
                "-e",
                "trace=%process,%network,%file",
                *command,
            ],
            env=env,
            expected=expected,
        )
        lines = raw.read_text().splitlines()
        execs = [line for line in lines if re.search(r"\bexecve(?:at)?\(", line)]
        network = [
            line
            for line in lines
            if re.search(
                r"\b(?:socket|connect|sendto|sendmsg|recvfrom|recvmsg|bind|listen|accept4?)\(",
                line,
            )
        ]
        writes = [
            line
            for line in lines
            if re.search(
                r"\b(?:open|openat|openat2)\(.*O_(?:WRONLY|RDWR|CREAT|TRUNC|APPEND)",
                line,
            )
            or re.search(
                r"\b(?:creat|mkdir|mkdirat|rename|renameat|renameat2|unlink|unlinkat|rmdir|symlink|symlinkat|link|linkat|truncate|chmod|fchmodat)\(",
                line,
            )
        ]
        processes = [
            line
            for line in lines
            if re.search(r"\b(?:clone|clone3|fork|vfork)\(", line)
            and "CLONE_THREAD" not in line
        ]
        forbidden = [
            line
            for line in execs
            if re.search(
                r'"[^" ]*/(?:mise|aqua|aqua-proxy|uv|uvx|nix|bazel|bazelisk)"', line
            )
        ]
        report["traces"][name] = {
            "argv": list(map(str, command)),
            "total_trace_lines": len(lines),
            "exec_events": execs,
            "nonthread_process_creation": processes,
            "network_events": network,
            "file_mutation_attempts": writes,
            "manager_exec_events": forbidden,
        }
        # Preserve reviewable significant events in the repository; full traces
        # remain in the disposable workspace, including ordinary file reads.
        significant = set(execs + network + writes + processes)
        (output / (name + ".events.log")).write_text(
            "\n".join(line for line in lines if line in significant) + "\n"
        )
        save()
        assert not forbidden, forbidden

    trace("native-version", [str(args.starpls), "version"])
    trace("python-version", [str(args.codespell), "--version"])
    trace("python-reference-version", [*reference, "--version"], env=reference_env)
    trace("python-typo", [str(args.codespell), str(typo)], expected=65)
    trace(
        "python-reference-typo", [*reference, str(typo)], env=reference_env, expected=65
    )

    for tool, exposed, underlying, env in [
        (
            "native",
            [str(args.starpls), "version"],
            [str(native), "version"],
            os.environ.copy(),
        ),
        (
            "python",
            [str(args.codespell), "--version"],
            [*reference, "--version"],
            reference_env,
        ),
    ]:
        samples = {"exposed": [], "underlying": []}
        expected_output = report["versions"][
            "starpls" if tool == "native" else "codespell"
        ]
        for index in range(args.samples + 3):
            routes = [("exposed", exposed, None), ("underlying", underlying, env)]
            if index % 2:
                routes.reverse()
            for route, command, environment in routes:
                start = time.perf_counter_ns()
                result = subprocess.run(
                    command, env=environment, capture_output=True, text=True, timeout=15
                )
                elapsed = (time.perf_counter_ns() - start) / 1e6
                assert (
                    result.returncode == 0 and result.stdout.strip() == expected_output
                )
                if index >= 3:
                    samples[route].append(elapsed)
        report["timings"][tool] = {
            "samples_ms": samples,
            "summary": {key: summarize(value) for key, value in samples.items()},
            "paired_delta_median_ms": statistics.median(
                a - b
                for a, b in zip(samples["exposed"], samples["underlying"], strict=True)
            ),
            "warmups_per_route": 3,
            "interleaved": True,
            "traced": False,
        }
        save()

    def interrupted(command, sig, environment):
        with subprocess.Popen(
            command,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        ) as process:
            try:
                # Wait until a thread is actually blocked reading our open stdin;
                # interrupting only the loader would not test the real tool.
                deadline = time.monotonic() + 5
                channels = []
                while time.monotonic() < deadline:
                    assert process.poll() is None, command
                    channels = [
                        path.read_text().strip()
                        for path in Path(f"/proc/{process.pid}/task").glob("*/wchan")
                    ]
                    if any("pipe_read" in channel for channel in channels):
                        break
                    time.sleep(0.01)
                assert any("pipe_read" in channel for channel in channels), channels
                process.send_signal(sig)
                status = process.wait(timeout=5)
                stdout, stderr = process.communicate(timeout=5)
                try:
                    os.killpg(process.pid, 0)
                    orphaned_group = True
                except ProcessLookupError:
                    orphaned_group = False
                assert not orphaned_group
                return {
                    "argv": command,
                    "signal": sig.name,
                    "ready_wchan": channels,
                    "exit": status,
                    "orphaned_process_group": orphaned_group,
                    "stdout": stdout.decode(errors="replace")[-1000:],
                    "stderr": stderr.decode(errors="replace")[-1000:],
                }
            finally:
                # Only this fresh session's process group can be cleaned up.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    for tool, exposed, underlying, environment in [
        (
            "native",
            [str(args.starpls), "server"],
            [str(native), "server"],
            os.environ.copy(),
        ),
        ("python", [str(args.codespell), "-"], [*reference, "-"], reference_env),
    ]:
        for sig in (signal.SIGTERM, signal.SIGINT):
            exposed_result = interrupted(exposed, sig, os.environ.copy())
            underlying_result = interrupted(underlying, sig, environment)
            assert exposed_result["exit"] == underlying_result["exit"]
            assert exposed_result["exit"] != 0
            report["signals"].append(
                {
                    "tool": tool,
                    "exposed": exposed_result,
                    "underlying": underlying_result,
                }
            )
            save()
    print(
        json.dumps(
            {
                "candidate": args.candidate,
                "versions": report["versions"],
                "traces": {
                    name: {
                        key: len(value)
                        for key, value in record.items()
                        if isinstance(value, list)
                    }
                    for name, record in report["traces"].items()
                },
                "timings": {
                    name: data["summary"] for name, data in report["timings"].items()
                },
                "signal_cases": len(report["signals"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
