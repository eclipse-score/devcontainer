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

# A literal Starlark dictionary lets Bazel consume the pins during analysis
# while ast.literal_eval preserves a data-only boundary for the root-running
# DevContainer installer.
PYTHON_TOOLS = {
    # The key is the public command and Bazel target name.
    "pre-commit": {
        # `package` is resolved by uv; `entrypoint` is the executable exposed to
        # users. They are separate because Python distributions may name them
        # differently.
        "package": "pre-commit",
        "version": "4.5.1",
        "entrypoint": "pre-commit",
        # Documentation is generated from the catalog so version and purpose
        # are reviewed together.
        "description": "Run repository pre-commit hooks",
    },
}
