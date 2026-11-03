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
export DEBIAN_FRONTEND=noninteractive

apt-get update

# environments.json selects the tools; providers.json names their extra setup scripts.
/usr/local/share/score-tools/internal/devcontainer/install.py install-environment bazel-feature --phase build
/usr/local/share/score-tools/internal/devcontainer/install.py install-environment bazel-feature
/usr/local/share/score-tools/internal/devcontainer/install.py install-environment bazel-feature --phase cleanup

apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
