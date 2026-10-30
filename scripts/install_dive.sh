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

echo "Installing dive..."

DIVE_NAME="/tmp/dive.deb"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
# Read the same owned definition used by the generated inventory. Quoting and
# variable-name validation happen in the stdlib-only metadata bridge.
score_dive_metadata="$(python3 "${SCRIPT_DIR}/../tools/internal/devcontainer/install.py" shell-metadata)"
eval "${score_dive_metadata}"
unset score_dive_metadata
VERSION="${dive_version}"

case "$(uname -m)" in
  x86_64) ARCH=amd64; SHA256SUM="${dive_amd64_sha256}" ;;
  aarch64|arm64) ARCH=arm64; SHA256SUM="${dive_arm64_sha256}" ;;
  *) echo "Unsupported architecture for dive" >&2; exit 1 ;;
esac

curl -L "https://github.com/wagoodman/dive/releases/download/v${VERSION}/dive_${VERSION}_linux_${ARCH}.deb" -o "${DIVE_NAME}"
echo "${SHA256SUM} /tmp/dive.deb" | sha256sum -c - || exit 1
sudo dpkg -i "${DIVE_NAME}"
rm -f "${DIVE_NAME}"

# Verify installation
dive --version
