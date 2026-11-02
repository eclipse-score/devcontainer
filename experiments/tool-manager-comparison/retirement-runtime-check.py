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
"""Execute real prepared tools with a hostile PATH through the current runner.

This checks the post-provisioning boundary. It neither provisions tools nor
claims that their full image build or host bootstrap has been exercised.
"""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=("mise", "aqua", "nix"), required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--bin", type=Path, required=True)
    parser.add_argument("--prefix-env", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runner = args.repo.resolve() / "tools/run-tool"
    prefix = args.bin.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "candidate": args.candidate,
        "runner_sha256": hashlib.sha256(runner.read_bytes()).hexdigest(),
        "prefix": str(prefix),
        "prefix_variable": args.prefix_env,
        "checks": [],
        "scope": "Prepared command execution; no bootstrap or fresh-image claim",
    }
    with tempfile.TemporaryDirectory(prefix="score-m5-direct-") as scratch:
        work = Path(scratch)
        poison = work / "poison"
        poison.mkdir()
        marker = work / "unexpected-path-call"
        # A strict call which picks arbitrary PATH, a manager, or Bazel must
        # fail observably. Existing missing-pin fallback has separate regressions.
        for name in ("mise", "aqua", "nix", "bazel", "uv", "uvx", "ruff", "pre-commit"):
            path = poison / name
            path.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$0" >> "$SCORE_M5_MARKER"\nexit 90\n'
            )
            path.chmod(0o755)
        env = {
            **os.environ,
            "RUN_TOOL_CONTAINER_MODE": "host",
            args.prefix_env: str(prefix),
            "PATH": f"{poison}:/usr/bin:/bin",
            "SCORE_M5_MARKER": str(marker),
        }
        (work / "bad input.py").write_text("missing_name\n")
        cases = [
            (name, ["--version"], 0) for name in ("uv", "uvx", "ruff", "pre-commit")
        ]
        cases.append(
            (
                "ruff",
                [
                    "check",
                    "--select",
                    "F821",
                    "--output-format",
                    "concise",
                    "bad input.py",
                ],
                1,
            )
        )
        for tool, flags, expected in cases:
            executable = prefix / tool
            assert executable.is_file() and os.access(executable, os.X_OK), executable
            direct = subprocess.run(
                [str(executable), *flags],
                cwd=work,
                env=env,
                capture_output=True,
                text=True,
            )
            strict = subprocess.run(
                ["/bin/bash", str(runner), "--strict", tool, *flags],
                cwd=work,
                env=env,
                capture_output=True,
                text=True,
            )
            check = {
                "tool": tool,
                "args": flags,
                "resolved_executable": str(executable.resolve()),
                "direct_exit": direct.returncode,
                "strict_exit": strict.returncode,
                "stdout": strict.stdout,
                "stderr": strict.stderr,
                "identical_results": (
                    direct.returncode == strict.returncode
                    and direct.stdout == strict.stdout
                    and direct.stderr == strict.stderr
                ),
            }
            report["checks"].append(check)
            output.write_text(json.dumps(report, indent=2) + "\n")
            assert direct.returncode == strict.returncode == expected, check
            assert check["identical_results"], check
            assert not marker.exists(), marker.read_text() if marker.exists() else ""
            if expected == 1:
                assert "F821" in strict.stdout and "bad input.py" in strict.stdout, (
                    check
                )
        report["unexpected_path_calls"] = []
        report["passed"] = True
        output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"{args.candidate}: direct and strict prepared invocations agree ({len(cases)} checks)"
    )


if __name__ == "__main__":
    main()
