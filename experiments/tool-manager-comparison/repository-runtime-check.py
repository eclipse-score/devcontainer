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
"""Shared external acceptance for prepared tooling and full DevContainer images.

Run in Docker with --network=none. Arguments are an expected-version
JSON file and the real checkout's tools/run-tool path. JSON has `profile`,
`versions` (command to exact version), and `bazel_version` from .bazelversion.
The outer invocation supplies the image's PATH and writable HOME/tmp. Optional
`expected_uid` selects the production development user; the tooling fixture's
default remains uid12345.
"""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    expectations = json.loads(Path(sys.argv[1]).read_text())
    runner = str(Path(sys.argv[2]).resolve())
    profile = expectations["profile"]
    versions = expectations["versions"]
    required = {
        "actionlint",
        "bazelisk",
        "buildifier",
        "ruff",
        "shellcheck",
        "uv",
        "uvx",
        "yamlfmt",
        "pre-commit",
    }
    assert profile in {"published", "repository"}
    if profile == "published":
        required |= {"pytest", "basedpyright"}
    assert set(versions) == required, (set(versions), required)
    assert os.getuid() == expectations.get("expected_uid", 12345)
    for manager in ("mise", "aqua", "nix"):
        assert shutil.which(manager) is None, manager
    if profile == "repository":
        for excluded in ("pytest", "basedpyright"):
            assert shutil.which(excluded) is None, excluded
    records = []
    work = Path(tempfile.mkdtemp(prefix="score-repository-runtime-"))
    (work / ".bazelversion").write_text(expectations["bazel_version"] + "\n")
    # Bazelisk discovers the version file relative to a recognized workspace;
    # the pin alone is insufficient in an otherwise empty consumer directory.
    (work / "MODULE.bazel").touch()
    os.chdir(work)

    def run(args, expected=0, env=None):
        result = subprocess.run(
            args, capture_output=True, text=True, env=env, check=False
        )
        records.append(
            {
                "argv": args,
                "exit": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        print(json.dumps(records[-1]), flush=True)
        assert result.returncode == expected, records[-1]
        return result.stdout + result.stderr

    flags = {
        "actionlint": ["-version"],
        "buildifier": ["-version"],
        "yamlfmt": ["-version"],
        "bazelisk": ["version"],
    }
    # The version flags differ upstream. Observe actual CLI output, and compare
    # both existing container runner modes with that same direct invocation.
    for tool in sorted(required):
        args = [tool, *flags.get(tool, ["--version"])]
        observed = run(args)
        pattern = r"(?<![\d.])" + re.escape(versions[tool]) + r"(?![\d.])"
        assert re.search(pattern, observed), (tool, observed)
        if tool == "bazelisk":
            assert expectations["bazel_version"] in observed, observed
        env = {**os.environ, "RUN_TOOL_CONTAINER_MODE": "container"}
        for mode in ([], ["--strict"]):
            wrapped = run([runner, *mode, *args], env=env)
            # Startup/cache diagnostics may differ on the first Bazel call.
            # Both modes must select the same expected CLI version.
            assert re.search(pattern, wrapped), (tool, mode, wrapped)
            if tool == "bazelisk":
                assert expectations["bazel_version"] in wrapped, wrapped

    run(["git", "init", "-q"])
    (work / "fixture with space.py").write_text("import os\n")
    (work / "fixture with space.sh").write_text("#!/bin/sh\necho $1\n")
    assert "F401" in run(["ruff", "check", "--isolated", "fixture with space.py"], 1)
    assert "SC2086" in run(["shellcheck", "fixture with space.sh"], 1)
    workflow = work / "invalid-workflow.yaml"
    workflow.write_text(
        "name: fixture\non: push\njobs:\n  fixture:\n    runs-on: ubuntu-latest\n    invalid-key: nope\n    steps:\n      - run: echo okay\n"
    )
    assert "invalid-key" in run(["actionlint", str(workflow)], 1)
    formatting = work / "format.yaml"
    formatting.write_text("foo:    bar\n")
    run(["yamlfmt", str(formatting)])
    assert formatting.read_text() == "foo: bar\n"
    starlark = work / "BUILD.bazel"
    unformatted = "x=[1,2]\n"
    starlark.write_text(unformatted)
    run(["buildifier", str(starlark)])
    formatted = starlark.read_text()
    assert formatted != unformatted
    # This fixture is valid in both Starlark and Python. Check its literal value
    # without prescribing BUILD-specific list layout or executing formatted code.
    assert ast.literal_eval(ast.parse(formatted).body[0].value) == [1, 2]
    run(["buildifier", "-mode=check", str(starlark)])
    (work / ".marker").touch()
    (work / ".pre-commit-config.yaml").write_text("""repos:
  - repo: local
    hooks:
      - id: cwd-and-args
        name: Consumer cwd and arguments
        language: system
        entry: sh -c 'test "$1" = "marker value" && test -f .marker' sh
        args: ['marker value']
        pass_filenames: false
        always_run: true
""")
    run(["git", "add", "."])
    run(["pre-commit", "run", "--all-files", "--verbose"])
    if profile == "published":
        (work / "test_selected.py").write_text(
            "def test_selected():\n    assert 6 * 7 == 42\n"
        )
        run(
            ["pytest", "-q", "test_selected.py"],
            env={**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
        )
        (work / "type_error.py").write_text('value: int = "wrong"\n')
        # Check an actual source error rather than merely the Node-backed
        # command's version; discovery stays inside this isolated consumer.
        diagnostic = run(
            ["basedpyright", "--pythonpath", sys.executable, "type_error.py"], 1
        )
        assert "reportAssignmentType" in diagnostic, diagnostic
    print(
        json.dumps(
            {
                "profile": profile,
                "result": "passed",
                "versions": versions,
                "uid": os.getuid(),
                "commands": len(records),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
