#!/usr/bin/env bash
set -euo pipefail

# Copy feature sources and tests to expected location
FEATURES_DIR="/devcontainer/features"
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")
mkdir -p "${FEATURES_DIR}"
COPY_TARGET="${FEATURES_DIR}/$(basename "${SCRIPT_DIR%%_*}")"
cp -R "${SCRIPT_DIR}" "${COPY_TARGET}"
rm -f "${COPY_TARGET}/devcontainer-features.env" "${COPY_TARGET}/devcontainer-features-install.sh"

DEBIAN_FRONTEND=noninteractive

# Read tool versions + metadata into environment variables
. /devcontainer/features/s-core-local/versions.sh

ARCHITECTURE=$(dpkg --print-architecture)

apt-get update

# INSTALL CONTAINER BUILD DEPENDENCIES
# Container build dependencies are not pinned, since they are removed anyway after container creation.
apt-get install apt-transport-https -y

# GraphViz
# The Ubuntu Noble package of GraphViz
apt-get install -y graphviz="${graphviz_version}*"

# Protobuf compiler, via APT (needed by FEO)
apt-get install -y protobuf-compiler="${protobuf_compiler_version}*"

# Bazelisk, directly from GitHub
# Using the existing devcontainer feature is not optimal:
# - it does not check the SHA256 checksum of the downloaded file
# - it cannot pre-install a specific version of Bazel, or prepare bash completion
BAZELISK_VARIANT="amd64"
SHA256SUM="${bazelisk_amd64_sha256}"
if [ "${ARCHITECTURE}" = "arm64" ]; then
    BAZELISK_VARIANT="aarch64"
    SHA256SUM="${bazelisk_arm64_sha256}"
fi
curl -L "https://github.com/bazelbuild/bazelisk/releases/download/v${bazelisk_version}/bazelisk-${BAZELISK_VARIANT}.deb" -o /tmp/bazelisk.deb
echo "${SHA256SUM} /tmp/bazelisk.deb" | sha256sum -c - || exit -1
apt-get install -y --no-install-recommends --fix-broken /tmp/bazelisk.deb
rm /tmp/bazelisk.deb

# Pre-install a fixed Bazel version, setup the bash command completion
USE_BAZEL_VERSION=${bazel_version}

bazel help completion bash > /tmp/bazel-complete.bash
ls -lah /tmp/bazel-complete.bash
mkdir -p /etc/bash_completion.d
mv /tmp/bazel-complete.bash /etc/bash_completion.d/bazel-complete.bash
sh -c "echo 'USE_BAZEL_VERSION=${bazel_version}' >> /etc/profile.d/bazel.sh"


# Starlark Language Server, directly from GitHub (apparently no APT repository available)
STARPLS_VARIANT="amd64"
SHA256SUM="${starpls_amd64_sha256}"
if [ "${ARCHITECTURE}" = "arm64" ]; then
    STARPLS_VARIANT="aarch64"
    SHA256SUM="${starpls_arm64_sha256}"
fi
curl -L "https://github.com/withered-magic/starpls/releases/download/v${starpls_version}/starpls-linux-${STARPLS_VARIANT}" -o /usr/local/bin/starpls
echo "${SHA256SUM} /usr/local/bin/starpls" | sha256sum -c - || exit -1
chmod +x /usr/local/bin/starpls

# Code completion for C++ code of Bazel projects
# (see https://github.com/kiron1/bazel-compile-commands)
# The version is pinned to a specific release, and the SHA256 checksum is provided by the devcontainer-features.json file.
source /etc/lsb-release
curl -L "https://github.com/kiron1/bazel-compile-commands/releases/download/v${bazel_compile_commands_version}/bazel-compile-commands_${bazel_compile_commands_version}-${DISTRIB_CODENAME}_${ARCHITECTURE}.deb" -o /tmp/bazel-compile-commands.deb
# Extract correct sha256 for current DISTRIB_CODENAME and check
SHA256SUM="${bazel_compile_commands_amd64_sha256}"
if [ "${ARCHITECTURE}" = "arm64" ]; then
    SHA256SUM="${bazel_compile_commands_arm64_sha256}"
fi
echo "${SHA256SUM} /tmp/bazel-compile-commands.deb" | sha256sum -c - || exit -1
apt-get install -y --no-install-recommends --fix-broken /tmp/bazel-compile-commands.deb
rm /tmp/bazel-compile-commands.deb

# Code completion for Rust code of Bazel projects (language server part)
# (see https://bazelbuild.github.io/rules_rust/rust_analyzer.html and https://rust-analyzer.github.io/book/rust_analyzer_binary.html)
# The version is pinned to a specific release, and the SHA256 checksum is provided by the devcontainer-features.json file.
# NOTE: For an unknown reason, rust-analyzer uses dates for downloading of releases, while the executable reports an actual release.
RUST_ANALYZER_VARIANT="x86_64"
SHA256SUM="${rust_analyzer_amd64_sha256}"
if [ "${ARCHITECTURE}" = "arm64" ]; then
    RUST_ANALYZER_VARIANT="aarch64"
    SHA256SUM="${rust_analyzer_arm64_sha256}"
fi
curl -L https://github.com/rust-lang/rust-analyzer/releases/download/${rust_analyzer_date}/rust-analyzer-${RUST_ANALYZER_VARIANT}-unknown-linux-gnu.gz > /tmp/rust-analyzer.gz
echo "${SHA256SUM} /tmp/rust-analyzer.gz" | sha256sum -c - || exit -1
gunzip -d /tmp/rust-analyzer.gz
mv /tmp/rust-analyzer /usr/local/bin/rust-analyzer
chmod +x /usr/local/bin/rust-analyzer

# qemu-system-arm
apt-get install -y --no-install-recommends --fix-broken qemu-system-arm="${qemu_system_arm_version}*"

# sshpass
apt-get install -y sshpass="${sshpass_version}*"

# Cleanup
# REMOVE CONTAINER BUILD DEPENDENCIES
apt-get remove --purge -y apt-transport-https
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
