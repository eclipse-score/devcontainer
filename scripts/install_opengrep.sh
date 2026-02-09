#!/usr/bin/env bash

set -euo pipefail

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

echo "installing opengrep..."

OPENGREP_NAME="/tmp/opengrep"

VERSION="1.15.1"

ARCHITECTURE="$(uname -m)"
if [ "${ARCHITECTURE}" = "x86_64" ]; then
  ARCH="x86"
  SHA256SUM="c4f6aab1edc8130c7a46e8f5e5215763420740fb94198fc9301215135a372900"
else
  ARCH="aarch64"
  SHA256SUM="08932db32f4cbfd6e3af6bda82adac41754275d18a91c0fe065181e6a5291be7"
fi

curl -L "https://github.com/opengrep/opengrep/releases/download/v${VERSION}/opengrep_manylinux_${ARCH}" -o /tmp/opengrep
echo "${SHA256SUM} /tmp/opengrep" | sha256sum -c - || exit 1
chmod +x "${OPENGREP_NAME}"
sudo mv /tmp/opengrep /usr/local/bin/opengrep

# Verify installation
opengrep --version
