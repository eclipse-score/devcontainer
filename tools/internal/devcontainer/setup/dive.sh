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

# install.py provides dive_version and per-architecture checksums as environment
# variables.
# shellcheck disable=SC2154
set -euo pipefail

ARCHITECTURE=$(dpkg --print-architecture)
case "${ARCHITECTURE}" in
    amd64)
        SHA256SUM="${dive_amd64_sha256}"
        ;;
    arm64)
        SHA256SUM="${dive_arm64_sha256}"
        ;;
    *)
        echo "No dive package selected for Linux ${ARCHITECTURE}" >&2
        exit 1
        ;;
esac

DEB="/tmp/dive.deb"
trap 'rm -f "${DEB}"' EXIT
curl -L "https://github.com/wagoodman/dive/releases/download/v${dive_version}/dive_${dive_version}_linux_${ARCHITECTURE}.deb" -o "${DEB}"
echo "${SHA256SUM} ${DEB}" | sha256sum -c -
apt-get install -y --no-install-recommends "${DEB}"

dive --version
