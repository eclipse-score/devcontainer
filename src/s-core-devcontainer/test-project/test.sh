#!/bin/bash
set -euo pipefail

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")
source "${SCRIPT_DIR}/../../../scripts/test-utils.sh" vscode

# Common tooling
check "validate git is working and has the correct version" bash -c "git --version | grep '2.49.0'"
check "validate git-lfs is working and has the correct version" bash -c "git lfs version | grep '3.7.0' "
check "validate python3 is working and has the correct version" bash -c "python3 --version | grep '3.12.11'"

# C++ tooling
check "validate clangd is working and has the correct version" bash -c "clangd --version | grep '20.1.8'"
check "validate clang-format is working and has the correct version" bash -c "clang-format --version | grep '20.1.8'"
check "validate clang-tidy is working and has the correct version" bash -c "clang-tidy --version | grep '20.1.8'"
check "validate clang is working and has the correct version" bash -c "clang --version | grep '20.1.8'"

# Bazel tooling
check "validate bazel is working and has the correct version" bash -c "bazel version | grep '8.4.1'"
check "validate bazelisk is working and has the correct version" bash -c "bazelisk version | grep '1.27.0'"
check "validate buildifier is working and has the correct version" bash -c "buildifier --version | grep '8.2.1'"

# Tests from the local s-core-local feature
source /devcontainer/features/s-core-local/tests/test_default.sh

# Report result
reportResults
