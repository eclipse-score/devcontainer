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

# install.py supplies catalog version variables in the process environment.
# shellcheck disable=SC2154
set -euo pipefail

ARCHITECTURE=$(dpkg --print-architecture)

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
