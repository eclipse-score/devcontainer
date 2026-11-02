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
"""Run the prepared-command audit in identical, network-isolated runtimes.

Payload paths must be complete M4 outputs, not single copied executables.
The writable workspace is new; candidate payloads and the root FS are read-only.
"""

import argparse
import json
import os
import platform
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--mise-payload", type=Path, required=True)
    parser.add_argument("--aqua-payload", type=Path, required=True)
    parser.add_argument("--nix-store", type=Path, required=True)
    parser.add_argument("--image", default="score-execution-audit:20261102")
    parser.add_argument("--samples", type=int, default=40)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = args.workspace.resolve()
    output.mkdir()  # Each complete run starts with fresh writable scratch space.
    image = subprocess.run(
        ["docker", "image", "inspect", args.image, "--format", "{{.Id}}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    provenance = {
        "image": args.image,
        "image_id": image,
        "host_architecture": platform.machine(),
        "samples_per_route": args.samples,
        "root_and_payloads_readonly": True,
        "network": "none",
        "uid": os.getuid(),
        "payloads": {},
    }
    assert os.getuid() != 0, (
        "Run as a normal host user to preserve the non-root runtime check"
    )
    payloads = {
        "mise": (args.mise_payload.resolve(), "/opt/score-tools"),
        "aqua": (args.aqua_payload.resolve(), "/opt/score-tools"),
        "nix": (args.nix_store.resolve(), "/nix/store"),
    }
    for candidate, (source, target) in payloads.items():
        assert source.is_dir(), source
        folder = output / candidate
        folder.mkdir()
        (folder / "input").mkdir()
        (folder / "input/clean.txt").write_text("the tool works\n")
        (folder / "input/typo.txt").write_text("teh tool works\n")
        policy = json.loads(
            (
                repo
                / f"experiments/tool-manager-comparison/maintenance-evidence/{candidate}.runtime.json"
            ).read_text()
        )
        commands = [command["argv"][0] for command in policy["commands"][:2]]
        provenance["payloads"][candidate] = {
            "source": str(source),
            "mount": target,
            "expected_versions": policy["versions"],
        }
        (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
        argv = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--tmpfs",
            "/tmp:rw,nosuid,nodev,mode=1777",
            "--mount",
            f"type=bind,src={source},dst={target},readonly",
            "--mount",
            f"type=bind,src={repo}/experiments/tool-manager-comparison/execution-probe.py,dst=/execution-probe.py,readonly",
            "--mount",
            f"type=bind,src={folder},dst=/work",
            "--workdir",
            "/work/input",
            "--env",
            "HOME=/tmp/probe-home",
            "--env",
            "PATH=/usr/bin:/bin",
            "--entrypoint",
            "python3",
            args.image,
            "/execution-probe.py",
            "--candidate",
            candidate,
            "--starpls",
            commands[0],
            "--codespell",
            commands[1],
            "--output",
            "/work",
            "--samples",
            str(args.samples),
        ]
        result = subprocess.run(argv, text=True, capture_output=True, timeout=120)
        (folder / "run.json").write_text(
            json.dumps(
                {
                    "argv": argv,
                    "exit": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                indent=2,
            )
            + "\n"
        )
        assert result.returncode == 0, result.stderr
        report = json.loads((folder / "results.json").read_text())
        assert report["versions"]["codespell"] == policy["versions"]["codespell"]
        print(
            candidate,
            json.dumps(
                {
                    "timings": {
                        name: data["summary"]
                        for name, data in report["timings"].items()
                    },
                    "signal_cases": len(report["signals"]),
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
