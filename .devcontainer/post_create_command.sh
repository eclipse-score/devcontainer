#!/usr/bin/env bash

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

npm install -g @devcontainers/cli

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

# Install uv and uvx from the native lockfile first. The pinned uv release then
# resolves every Python distribution declared in the shared catalog.
sudo "${REPOSITORY_ROOT}/tools/internal/devcontainer/install.py" install actionlint bazelisk buildifier ruff shellcheck uv uvx yamlfmt

# Install the catalogued Python distribution system-wide. The explicit
# directories avoid root-specific uv defaults and make pre-commit available to
# the non-root development user.
sudo "${REPOSITORY_ROOT}/tools/internal/devcontainer/install.py" install-python pre-commit \
    --bin-dir /usr/local/bin --tool-dir /usr/local/share/uv/tools

# Hooks can only be registered after the catalogued executable is on PATH.
pre-commit install

scripts/create_builder.sh
