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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"
SCORE_TOOLS_PREFIX="${HOME}/.local/share/score-tools"
export SCORE_TOOLS_BIN="${SCORE_TOOLS_PREFIX}/bin"
export PATH="${SCORE_TOOLS_BIN}:${PATH}"

# The generic Node DevContainer image does not include the repository tool set.
# The provisioner checks its owner snapshot and returns immediately when this
# user's direct prefix is current; a stale or missing prefix is refreshed from
# the production owners before the remaining OS/npm providers are applied.
python3 "${REPOSITORY_ROOT}/tools/internal/devcontainer/provision_host_tools.py" \
    --profile repository \
    --prefix "${SCORE_TOOLS_PREFIX}"

sudo "${REPOSITORY_ROOT}/tools/internal/devcontainer/install.py" environment repository

# Hooks can only be registered after the catalogued executable is on PATH.
pre-commit install

scripts/create_builder.sh
