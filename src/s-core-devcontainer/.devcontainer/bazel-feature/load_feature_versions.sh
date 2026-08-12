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

ARCHITECTURE=$(dpkg --print-architecture)
VERSION="v4.47.2"

SHA256_FIELD="1bb99e1019e23de33c7e6afc23e93dad72aad6cf2cb03c797f068ea79814ddb0" # Default to amd64
if [ "${ARCHITECTURE}" = "arm64" ]; then
  SHA256_FIELD="05df1f6aed334f223bb3e6a967db259f7185e33650c3b6447625e16fea0ed31f"
fi

# if /tmp/yq does not exist, download yq
if [ ! -f /tmp/yq ]; then
  curl -L "https://github.com/mikefarah/yq/releases/download/${VERSION}/yq_linux_${ARCHITECTURE}" -o /tmp/yq
  echo "${SHA256_FIELD} /tmp/yq" | sha256sum -c - || exit 1
  chmod +x /tmp/yq
fi

# Read tool versions and metadata into environment variables
export $(/tmp/yq eval '.. | select((tag == "!!map" or tag == "!!seq") | not) | (path | join("_")) + "=" + .' "$1" | awk '!/=$/{print }' | xargs)

# Clean up
trap 'rm -f /tmp/yq' EXIT
