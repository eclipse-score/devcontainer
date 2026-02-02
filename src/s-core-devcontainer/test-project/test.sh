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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -euo pipefail

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")

source "${SCRIPT_DIR}/test-utils.sh" vscode

# C++ tooling
check "validate clangd is working and has the correct version" bash -c "clangd --version | grep '20.1.8'"
check "validate clang-format is working and has the correct version" bash -c "clang-format --version | grep '20.1.8'"
check "validate clang-tidy is working and has the correct version" bash -c "clang-tidy --version | grep '20.1.8'"
check "validate clang is working and has the correct version" bash -c "clang --version | grep '20.1.8'"

# Rust tooling
check "validate rustc is working and has the correct version" bash -c "rustc --version | grep '1.83.0'"
check "validate cargo is working and has the correct version" bash -c "cargo --version | grep '1.83.0'"
check "validate cargo clippy is working and has the correct version" bash -c "cargo clippy --version | grep '0.1.83'"
check "validate rustfmt is working and has the correct version" bash -c "rustfmt --version | grep '1.8.0-stable'"
check "validate rust-analyzer is working and has the correct version" bash -c "rust-analyzer --version | grep '1.83.0'"

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
