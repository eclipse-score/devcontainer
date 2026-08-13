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

"""Expose pinned Python CLIs without requiring Python on the Bazel host.

The catalog is loaded during analysis so the runtime launcher only needs the
shell and the pinned uvx executable supplied by rules_multitool.
"""

load("@rules_shell//shell:sh_binary.bzl", "sh_binary")
load(":lockfiles/python_tools.bzl", "PYTHON_TOOLS")

def python_tool(name):
    """Creates a runnable target from the shared Python tool catalog."""

    # Fail during analysis so a misspelled target cannot degrade into an
    # unpinned uvx invocation at runtime.
    if name not in PYTHON_TOOLS:
        fail("Python tool '{}' is not defined in python_tools.bzl".format(name))

    tool = PYTHON_TOOLS[name]

    # These fields cross the Starlark-to-shell boundary. Validate them here to
    # produce a catalog error rather than an opaque launcher failure.
    for field in ("package", "version", "entrypoint"):
        value = tool.get(field)
        if type(value) != "string" or not value:
            fail("Python tool '{}' requires a non-empty '{}'".format(name, field))

    sh_binary(
        name = name,
        srcs = ["internal/run_python_tool.sh"],
        # Rule arguments are prepended to user arguments. The launcher receives
        # the runfiles-resolved uvx binary followed by immutable catalog data.
        args = [
            "$(location :uvx_binary)",
            "{}=={}".format(tool["package"], tool["version"]),
            tool["entrypoint"],
        ],
        # uvx is data rather than a host PATH lookup so rules_multitool controls
        # its version and platform selection.
        data = [":uvx_binary"],
    )
