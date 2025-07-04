#!/usr/bin/env bash
set -euo pipefail

# Common tooling
check "validate graphviz is working" bash -c "dot -V"
check "validate curl is working" bash -c "curl --version"

# Bazel and related tools
check "validate bazel is working" bash -c "bazel version"
check "validate bazel-compile-commands is working" bash -c "bazel-compile-commands --version"
check "validate buildifier is working" bash -c "buildifier --version"

# Rust tooling
check "validate rust-analyzer is working" bash -c "rust-analyzer --version"

# Other build-related tools
check "validate protoc is working" bash -c "protoc --version"
