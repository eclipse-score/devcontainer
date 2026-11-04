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

"""Let Bazel read the same JSON package definitions as the container installer."""

def _catalog_repository_impl(repository_ctx):
    definitions = json.decode(repository_ctx.read(repository_ctx.attr.definitions))
    if type(definitions) != "dict":
        fail("Tool providers must be a dictionary")
    tools = {}
    for name, definition in definitions.items():
        if type(definition) != "dict":
            fail("Invalid provider definition for '{}'".format(name))
        if definition.get("provider") != "python":
            continue
        tool = {}
        for field in ("package", "version", "entrypoint", "description"):
            value = definition.get(field)
            if type(value) != "string" or not value:
                fail("Malformed Python package definition for '{}'".format(name))
            tool[field] = value
        dependencies = definition.get("requires", [])
        if type(dependencies) != "list" or "uv" not in dependencies:
            fail("Python tool '{}' must declare its uv dependency".format(name))
        tools[name] = tool

    # BUILD macros cannot read JSON source files. Produce their Starlark input
    # inside Bazel's repository cache, directly from the tracked JSON file.
    # repr quotes every string as data; catalog values cannot become code.
    repository_ctx.file("python_tools.bzl", "PYTHON_TOOLS = " + repr(tools) + "\n")
    repository_ctx.file("BUILD.bazel", 'exports_files(["python_tools.bzl"])\n')

# The label is an explicit input: changing providers.json refreshes the generated
# data. No Python interpreter, network download or checked-in copy is needed.
catalog_repository = repository_rule(
    implementation = _catalog_repository_impl,
    attrs = {"definitions": attr.label(mandatory = True, allow_single_file = True)},
)
