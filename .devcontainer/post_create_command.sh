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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

# npm's global directory belongs to the development user in the Node.js base
# image. Keep npm setup in that user's environment; system tools require root.
"${REPOSITORY_ROOT}/tools/internal/devcontainer/install.py" install-environment repository-devcontainer --providers npm
sudo "${REPOSITORY_ROOT}/tools/internal/devcontainer/install.py" install-environment repository-devcontainer --providers native python

# Hooks can only be registered after the catalogued executable is on PATH.
pre-commit install

scripts/create_builder.sh
