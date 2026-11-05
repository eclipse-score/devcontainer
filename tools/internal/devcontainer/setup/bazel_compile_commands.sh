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

# Install the helper that generates compile_commands.json for Bazel projects.
# install.py supplies the release version and per-CPU checksums as environment
# variables: bazel_compile_commands_version and bazel_compile_commands_*_sha256.
# shellcheck disable=SC2154
set -euo pipefail

ARCHITECTURE=$(dpkg --print-architecture)

# Install the helper that writes compile_commands.json for editors using Bazel.
# (see https://github.com/kiron1/bazel-compile-commands)
source /etc/lsb-release
curl -L "https://github.com/kiron1/bazel-compile-commands/releases/download/v${bazel_compile_commands_version}/bazel-compile-commands_${bazel_compile_commands_version}-${DISTRIB_CODENAME}_${ARCHITECTURE}.deb" -o /tmp/bazel-compile-commands.deb
# Check the checksum for this CPU before installing the downloaded package.
SHA256SUM="${bazel_compile_commands_amd64_sha256}"
if [ "${ARCHITECTURE}" = "arm64" ]; then
    SHA256SUM="${bazel_compile_commands_arm64_sha256}"
fi
echo "${SHA256SUM} /tmp/bazel-compile-commands.deb" | sha256sum -c - || exit 1
apt-get install -y --no-install-recommends --fix-broken /tmp/bazel-compile-commands.deb
rm /tmp/bazel-compile-commands.deb
