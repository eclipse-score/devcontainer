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
"""Run a catalogued Python command using caller-supplied uv.

Only tool selection is owned here. uv resolves the interpreter and transitive
packages; the top-level pin does not claim a fully locked Python environment.
"""

import os
import shutil
import sys

from .catalog import _load_python_tools


def main():
    tools = _load_python_tools()
    arguments = sys.argv[1:]
    if not arguments or arguments[0] in ("--help", "-h"):
        print(
            "Usage: score-tool COMMAND [ARG ...]\nCommands: " + ", ".join(sorted(tools))
        )
        return 0
    command, *arguments = arguments
    if command not in tools:
        print(f"Unknown Python tool: {command}", file=sys.stderr)
        return 2
    uv = shutil.which("uv")
    if uv is None:
        print("score-tool requires compatible uv on PATH", file=sys.stderr)
        return 127
    tool = tools[command]
    # exec preserves cwd, signals, argument boundaries and the tool exit status.
    os.execv(
        uv,
        [
            uv,
            "tool",
            "run",
            "--from",
            f"{tool['package']}=={tool['version']}",
            tool["entrypoint"],
            *arguments,
        ],
    )
