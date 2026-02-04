#!/usr/bin/env bash

# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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

PRE_COMMIT_CONFIG_FILE=".pre-commit-config.yaml"

if [[ -f "${PRE_COMMIT_CONFIG_FILE}" ]]
then
    echo "Pre-commit configuration found (${PRE_COMMIT_CONFIG_FILE})"
    "${PIPX_BIN_DIR}/pre-commit" install
else
    echo "No pre-commit configuration found (${PRE_COMMIT_CONFIG_FILE})"
    echo "Skipping pre-commit hook's installation"
fi
