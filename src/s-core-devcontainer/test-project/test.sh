#!/bin/bash
set -euo pipefail

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")
source "${SCRIPT_DIR}/../../../scripts/test-utils.sh" vscode

# Common tooling
check "validate git is working and has the correct version" bash -c "git --version | grep '2.49.0'"
check "validate git-lfs is working and has the correct version" bash -c "git lfs version | grep '3.7.0'"

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

# Report result
reportResults
