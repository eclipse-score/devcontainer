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

# Generated versions from tools/owners/aqua/pyproject.toml.
# Descriptions/public command identities retain the existing catalog contract.
PYTHON_TOOLS = {
    "pre-commit": {
        "package": "pre-commit",
        "version": "4.7.0",
        "entrypoint": "pre-commit",
        "description": "Run repository pre-commit hooks",
    },
    "basedpyright": {
        "package": "basedpyright",
        "version": "1.35.0",
        "entrypoint": "basedpyright",
        "entrypoints": ["basedpyright", "basedpyright-langserver"],
        "description": "Type check Python and provide its language server",
    },
    "pytest": {
        "package": "pytest",
        "version": "9.0.2",
        "entrypoint": "pytest",
        "entrypoints": ["pytest", "py.test"],
        "description": "Run Python tests",
    },
    "codespell": {
        "package": "codespell",
        "entrypoint": "codespell",
        "description": "Check source files for common misspellings",
        "version": "2.4.1",
    },
}
