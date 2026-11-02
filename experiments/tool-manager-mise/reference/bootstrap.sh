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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# Producer bootstrap only. The prepared Ubuntu runtime never contains mise.
set -euo pipefail
prefix="${1:?isolated bootstrap directory required}"
mkdir -p "${prefix}"
if [[ -n "${SCORE_MISE_BOOTSTRAP_BINARY:-}" ]]; then
    cp -- "${SCORE_MISE_BOOTSTRAP_BINARY}" "${prefix}/mise"
else
    curl --fail --location --output "${prefix}/mise" \
        https://github.com/jdx/mise/releases/download/v2026.10.24/mise-v2026.10.24-linux-x64
fi
printf '%s  %s\n' be97dbac1c0b1fe08bd8c0cf01690f4273ea9aa02ad766b98d4e20c43eb9059d "${prefix}/mise" | sha256sum -c -
chmod +x "${prefix}/mise"
