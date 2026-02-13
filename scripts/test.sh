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

set -euxo pipefail

IMAGE="s-core-devcontainer"

export DOCKER_BUILDKIT=1

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")
PROJECT_DIR=$(dirname -- "${SCRIPT_DIR}")
ID_LABEL="test-container=${IMAGE}"

. "${SCRIPT_DIR}/functions.sh"
set_dockerfile_name

devcontainer up \
  --id-label "${ID_LABEL}" \
  --workspace-folder "${PROJECT_DIR}/src/${IMAGE}/" \
  --remove-existing-container

# Run actual test
echo "(*) Running test..."
devcontainer exec --workspace-folder "${PROJECT_DIR}/src/${IMAGE}" --id-label "${ID_LABEL}" \
  /bin/sh -c 'set -e && cd test-project && \
  ./test.sh'
