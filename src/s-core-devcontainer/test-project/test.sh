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

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")

source "${SCRIPT_DIR}/test-utils.sh" vscode

# System headers for non-hermetic Bazel toolchains
package_installed() {
    test "$(dpkg-query -W -f='${db:Status-Status}' "$1")" = installed
}
check "validate libstdc++ development package is installed" package_installed libstdc++-13-dev
check "validate libc development package is installed" package_installed libc6-dev

# System trust store. Verifies the Dockerfile's CA refresh, so it is sourced
# explicitly here rather than being discovered; forgetting this line skips it.
source "${SCRIPT_DIR}/ca_certificates.sh"

# Tests from the local s-core-local feature
source /devcontainer/features/s-core-local/tests/test_default.sh

# Tests from the local bazel feature
source /devcontainer/features/bazel/tests/test_default.sh

# Check that no environment variables are empty
. /etc/bash_completion
for var in $(compgen -e); do
    if [[ "${var}" == "LS_COLORS" ]]; then
        continue
    fi
    check "validate environment variable ${var} is not empty" bash -c "[ -n \"\${${var}}\" ]"
done

# Report result
reportResults
