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

REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -z "${REPO_ROOT}" ]]
then
    echo "Could not determine repository root, skipping OpenCode config sync"
    exit 0
fi

STAGED_OPENCODE_CONFIG_DIR="${REPO_ROOT}/src/s-core-devcontainer/.devcontainer/.host-config/opencode"
TARGET_OPENCODE_CONFIG_DIR="/home/vscode/.config/opencode"

if [[ ! -d "${STAGED_OPENCODE_CONFIG_DIR}" ]]
then
    echo "No staged OpenCode config found (${STAGED_OPENCODE_CONFIG_DIR})"
    echo "Skipping OpenCode config sync"
    exit 0
fi

if [[ -z "$(find "${STAGED_OPENCODE_CONFIG_DIR}" -mindepth 1 -print -quit 2>/dev/null)" ]]
then
    echo "Staged OpenCode config is empty (${STAGED_OPENCODE_CONFIG_DIR})"
    echo "Skipping OpenCode config sync"
    exit 0
fi

mkdir -p "$(dirname "${TARGET_OPENCODE_CONFIG_DIR}")"
rm -rf "${TARGET_OPENCODE_CONFIG_DIR}"
mkdir -p "${TARGET_OPENCODE_CONFIG_DIR}"
cp -a "${STAGED_OPENCODE_CONFIG_DIR}/." "${TARGET_OPENCODE_CONFIG_DIR}/"
rm -rf "${STAGED_OPENCODE_CONFIG_DIR}"

echo "Synced OpenCode config to ${TARGET_OPENCODE_CONFIG_DIR}"
