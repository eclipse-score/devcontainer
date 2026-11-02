#!/usr/bin/env bash
# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

# Refresh mise artifact locks and every generated compatibility consumer.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/../../.." && pwd -P)"
TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/score-mise-refresh.XXXXXX")"
trap 'rm -rf -- "${TEMP_DIR}"' EXIT

if [[ -n "${MISE_BINARY:-}" ]]; then
    binary="${MISE_BINARY}"
else
    bash "${SCRIPT_DIR}/bootstrap.sh" "${TEMP_DIR}/mise"
    binary="${TEMP_DIR}/mise/mise"
fi

cd -- "${REPOSITORY_ROOT}"
MISE_BINARY="${binary}" python3 tools/internal/mise/refresh.py --refresh
python3 tools/internal/sync_readme.py
