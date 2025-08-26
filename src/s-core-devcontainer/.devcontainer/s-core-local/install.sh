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

apt-get update

# INSTALL CONTAINER BUILD DEPENDENCIES
# Container build dependencies are not pinned, since they are removed anyway after container creation.
apt-get install apt-transport-https -y

# GraphViz
# The Ubuntu Noble package of GraphViz
apt-get install -y graphviz="${graphviz_version}*"

# Protobuf compiler, via APT (needed by FEO)
apt-get install -y protobuf-compiler="${protobuf_compiler_version}*"

# Bazel, via APT
# - ghcr.io/devcontainers-community/features/bazel uses bazelisk, which has a few problems:
#   - It does not install bash autocompletion.
#   - The bazel version is not pinned, which is required to be reproducible and to have coordinated, tested tool updates.
#   - In general, pre-built containers *shall not* download "more tools" from the internet.
#     This is an operational risk (security, availability); it makes the build non-reproducible,
#     and it prevents the container from working in air-gapped environments.
curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor > bazel-archive-keyring.gpg
mv bazel-archive-keyring.gpg /usr/share/keyrings
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8" | tee /etc/apt/sources.list.d/bazel.list
apt-get update
apt-get install -y bazel=${bazel_version}

# Buildifier, directly from GitHub (apparently no APT repository available)
# The version is pinned to a specific release, and the SHA256 checksum is provided by the devcontainer-features.json file.
curl -L "https://github.com/bazelbuild/buildtools/releases/download/v${buildifier_version}/buildifier-linux-amd64" -o /usr/local/bin/buildifier
echo "${buildifier_amd64_sha256} /usr/local/bin/buildifier" | sha256sum -c - || exit -1
chmod +x /usr/local/bin/buildifier

# Starlark Language Server, directly from GitHub (apparently no APT repository available)
curl -L "https://github.com/withered-magic/starpls/releases/download/v${starpls_version}/starpls-linux-amd64" -o /usr/local/bin/starpls
echo "${starpls_amd64_sha256} /usr/local/bin/starpls" | sha256sum -c - || exit -1
chmod +x /usr/local/bin/starpls

# Code completion for C++ code of Bazel projects
# (see https://github.com/kiron1/bazel-compile-commands)
# The version is pinned to a specific release, and the SHA256 checksum is provided by the devcontainer-features.json file.
source /etc/lsb-release
curl -L "https://github.com/kiron1/bazel-compile-commands/releases/download/v${bazel_compile_commands_version}/bazel-compile-commands_${bazel_compile_commands_version}-${DISTRIB_CODENAME}_amd64.deb" -o /tmp/bazel-compile-commands.deb
# Extract correct sha256 for current DISTRIB_CODENAME and check
echo "${bazel_compile_commands_amd64_sha256} /tmp/bazel-compile-commands.deb" | sha256sum -c - || exit -1
apt-get install -y --no-install-recommends --fix-broken /tmp/bazel-compile-commands.deb
rm /tmp/bazel-compile-commands.deb

# Code completion for Rust code of Bazel projects (language server part)
# (see https://bazelbuild.github.io/rules_rust/rust_analyzer.html and https://rust-analyzer.github.io/book/rust_analyzer_binary.html)
# The version is pinned to a specific release, and the SHA256 checksum is provided by the devcontainer-features.json file.
# NOTE: For an unknown reason, rust-analyzer uses dates for downloading of releases, while the executable reports an actual release.
curl -L https://github.com/rust-lang/rust-analyzer/releases/download/${rust_analyzer_date}/rust-analyzer-x86_64-unknown-linux-gnu.gz > /tmp/rust-analyzer.gz
echo "${rust_analyzer_amd64_sha256} /tmp/rust-analyzer.gz" | sha256sum -c - || exit -1
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
