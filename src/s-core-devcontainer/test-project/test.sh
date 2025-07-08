#!/bin/bash
set -euo pipefail

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")
source "${SCRIPT_DIR}/../../../scripts/test-utils.sh" vscode

# Common tooling
check "validate git is working" bash -c "git --version"
check "validate git-lfs is working" bash -c "git lfs version"
check "validate python3 is working" bash -c "python3 --version"

# C++ tooling
check "validate clangd is working" bash -c "clangd --version"
check "validate clang-format is working" bash -c "clang-format --version"
check "validate clang-tidy is working" bash -c "clang-tidy --version"
check "validate clang is working" bash -c "clang --version"

# Tests from the local s-core-local feature
source /devcontainer/features/s-core-local/tests/test_default.sh

# Report result
reportResults
