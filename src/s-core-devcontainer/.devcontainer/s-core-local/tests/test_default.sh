#!/usr/bin/env bash
set -euo pipefail

# Read tool versions + metadata into environment variables
. /devcontainer/features/s-core-local/versions.sh

# Common tooling
# For an unknown reason, dot -V reports on Ubuntu Noble a version 2.43.0, while the package has a different version.
# Hence, we have to work around that.
check "validate graphviz is working" bash -c "dot -V"
check "validate graphviz has the correct version" bash -c "dpkg -s graphviz | grep 'Version: ${graphviz_version}'"

# Other build-related tools
check "validate protoc is working and has the correct version" bash -c "protoc --version | grep 'libprotoc ${protobuf_compiler_version}'"

# Bazel-related tools
check "validate starpls is working and has the correct version" bash -c "starpls version | grep '${starpls_version}'"
check "validate bazel-compile-commands is working and has the correct version" bash -c "bazel-compile-commands --version 2>&1 | grep '${bazel_compile_commands_version}'"

# Rust tooling
check "validate rust-analyzer is working and has the correct version" bash -c "rust-analyzer --version 2>&1 | grep '${rust_analyzer_version}'"

# Qemu target-related tools
check "validate qemu-system-aarch64 is working and has the correct version" bash -c "qemu-system-aarch64 --version | grep '${qemu_system_arm_version}'"
check "validate sshpass is working and has the correct version" bash -c "sshpass -V | grep '${sshpass_version}'"
