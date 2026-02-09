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
# SPDX-FileCopyrightText: Copyright (c) 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -euo pipefail

# Copy feature sources and tests to expected location
FEATURES_DIR="/devcontainer/features"
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")
mkdir -p "${FEATURES_DIR}"
COPY_TARGET="${FEATURES_DIR}/$(basename "${SCRIPT_DIR%%_*}")"
cp -R "${SCRIPT_DIR}" "${COPY_TARGET}"
rm -f "${COPY_TARGET}/devcontainer-features.env" "${COPY_TARGET}/devcontainer-features-install.sh"

# shellcheck disable=SC2034
# used by apt-get only inside this script
DEBIAN_FRONTEND=noninteractive

# Read tool versions + metadata into environment variables
. /devcontainer/features/s-core-local/versions.sh /devcontainer/features/bazel/versions.yaml

ARCHITECTURE=$(dpkg --print-architecture)

apt-get update

# INSTALL CONTAINER BUILD DEPENDENCIES
# Container build dependencies are not pinned, since they are removed anyway after container creation.
apt-get install apt-transport-https -y

# Bazelisk, directly from GitHub
# Using the existing devcontainer feature is not optimal:
# - it does not check the SHA256 checksum of the downloaded file
# - it cannot pre-install a specific version of Bazel, or prepare bash completion
BAZELISK_VARIANT="amd64"
SHA256SUM="${bazelisk_amd64_sha256}"
if [ "${ARCHITECTURE}" = "arm64" ]; then
    BAZELISK_VARIANT="arm64"
    SHA256SUM="${bazelisk_arm64_sha256}"
fi
curl -L "https://github.com/bazelbuild/bazelisk/releases/download/v${bazelisk_version}/bazelisk-${BAZELISK_VARIANT}.deb" -o /tmp/bazelisk.deb
echo "${SHA256SUM} /tmp/bazelisk.deb" | sha256sum -c - || exit 1
apt-get install -y --no-install-recommends --fix-broken /tmp/bazelisk.deb
rm /tmp/bazelisk.deb

# Pre-install a fixed Bazel version, setup the bash command completion
export USE_BAZEL_VERSION=${bazel_version}
# bazelisk downloads Bazel into the home directory of the user running the command
# lets assume there is only one user in the devcontainer
su $(ls /home) -c "bazel help completion bash > /tmp/bazel-complete.bash"
mkdir -p /etc/bash_completion.d
mv /tmp/bazel-complete.bash /etc/bash_completion.d/bazel-complete.bash
sh -c "echo 'INSTALLED_BAZEL_VERSION=${bazel_version}' >> /devcontainer/features/bazel/bazel_setup.sh"

# Configure Bazel to use system trust store for SSL/TLS connections
# This is required for corporate environments with custom CA certificates
echo 'startup --host_jvm_args=-Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts --host_jvm_args=-Djavax.net.ssl.trustStorePassword=changeit' >> /etc/bazel.bazelrc

# Buildifier, directly from GitHub (apparently no APT repository available)
# The version is pinned to a specific release, and the SHA256 checksum is provided by the devcontainer-features.json file.
BUILDIFIER_VARIANT="amd64"
SHA256SUM="${buildifier_amd64_sha256}"
if [ "${ARCHITECTURE}" = "arm64" ]; then
    BUILDIFIER_VARIANT="arm64"
    SHA256SUM="${buildifier_arm64_sha256}"
fi
curl -L "https://github.com/bazelbuild/buildtools/releases/download/v${buildifier_version}/buildifier-linux-${BUILDIFIER_VARIANT}" -o /usr/local/bin/buildifier
echo "${SHA256SUM} /usr/local/bin/buildifier" | sha256sum -c - || exit 1
chmod +x /usr/local/bin/buildifier

# Starlark Language Server, directly from GitHub (apparently no APT repository available)
STARPLS_VARIANT="amd64"
SHA256SUM="${starpls_amd64_sha256}"
if [ "${ARCHITECTURE}" = "arm64" ]; then
    STARPLS_VARIANT="aarch64"
    SHA256SUM="${starpls_arm64_sha256}"
fi
curl -L "https://github.com/withered-magic/starpls/releases/download/v${starpls_version}/starpls-linux-${STARPLS_VARIANT}" -o /usr/local/bin/starpls
echo "${SHA256SUM} /usr/local/bin/starpls" | sha256sum -c - || exit 1
chmod +x /usr/local/bin/starpls

# Code completion for C++ code of Bazel projects
# (see https://github.com/kiron1/bazel-compile-commands)
source /etc/lsb-release
curl -L "https://github.com/kiron1/bazel-compile-commands/releases/download/v${bazel_compile_commands_version}/bazel-compile-commands_${bazel_compile_commands_version}-${DISTRIB_CODENAME}_${ARCHITECTURE}.deb" -o /tmp/bazel-compile-commands.deb
# Extract correct sha256 for current DISTRIB_CODENAME and check
SHA256SUM="${bazel_compile_commands_amd64_sha256}"
if [ "${ARCHITECTURE}" = "arm64" ]; then
    SHA256SUM="${bazel_compile_commands_arm64_sha256}"
fi
echo "${SHA256SUM} /tmp/bazel-compile-commands.deb" | sha256sum -c - || exit 1
apt-get install -y --no-install-recommends --fix-broken /tmp/bazel-compile-commands.deb
rm /tmp/bazel-compile-commands.deb

# Cleanup
# REMOVE CONTAINER BUILD DEPENDENCIES
apt-get remove --purge -y apt-transport-https
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
