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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -eo pipefail

if [[ -z ${HOME} ]]; then
    HOME="/root"
fi

FAILED=()

echoStderr()
{
    echo "$@" 1>&2
}

check() {
    LABEL=$1
    shift
    echo -e "\n🧪 Testing ${LABEL}"
    if "$@"; then
        echo "✅  Passed!"
        return 0
    else
        echoStderr "❌ ${LABEL} check failed."
        FAILED+=("${LABEL}")
        return 1
    fi
}

reportResults() {
    if [[ ${#FAILED[@]} -ne 0 ]]; then
        echoStderr -e "\n💥  Failed tests:" "${FAILED[@]}"
        exit 1
    else
        echo -e "\n💯  All passed!"
        exit 0
    fi
}
