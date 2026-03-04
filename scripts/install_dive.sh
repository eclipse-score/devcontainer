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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

echo "Installing dive..."

DIVE_NAME="/tmp/dive.deb"

VERSION="0.13.1"

ARCHITECTURE="$(uname -m)"
if [ "${ARCHITECTURE}" = "x86_64" ]; then
  ARCH="amd64"
  SHA256SUM="0c20d18f0cc87e6e982a3289712ac3aa9fc364ba973109d1da3a473232640571"
else
  ARCH="arm64"
  SHA256SUM="80203401b3d7c4feffd13575755a07834a2d2f35f49e8612f0749b318c3f2fa5"
fi

curl -L "https://github.com/wagoodman/dive/releases/download/v${VERSION}/dive_${VERSION}_linux_${ARCH}.deb" -o "${DIVE_NAME}"
echo "${SHA256SUM} /tmp/dive.deb" | sha256sum -c - || exit 1
sudo dpkg -i "${DIVE_NAME}"
rm -f "${DIVE_NAME}"

# Verify installation
dive --version
