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

set -euxo pipefail

# Usage: test_consumer.sh <repo-url> [revision] [devcontainer-image]
# Tests that a consumer repository can be built and tested using the devcontainer.
# It is checked that these commands work without errors:
#   - bazel build //...
#   - bazel test //...
# Parameters:
#   repo-url             : Git URL of the consumer repository
#   revision             : Git branch/tag/commit (default: main)

REPO_URL="${1:?Repository URL is required}"
REVISION="${2:-main}"

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

# Extract repo name from URL
REPO_NAME=$(basename "${REPO_URL}" .git)
REPO_WORKSPACE="/tmp/${REPO_NAME}"

echo "(*) Cloning repository..."
# --revision not supported by older git versions, so we clone first and then checkout the revision
# devcontainer exec --id-label "${ID_LABEL}" git clone --depth 1 --revision "${REVISION}" "${REPO_URL}" "${REPO_WORKSPACE}"
devcontainer exec --id-label "${ID_LABEL}" git clone "${REPO_URL}" "${REPO_WORKSPACE}"
devcontainer exec --id-label "${ID_LABEL}" git -C "${REPO_WORKSPACE}" checkout "${REVISION}"

# Run build and test with Bazel using docker exec
echo "(*) Running Bazel build in devcontainer..."
devcontainer exec --id-label="${ID_LABEL}" /bin/sh -c "set -e && cd \"${REPO_WORKSPACE}\" && bazel build //..."

echo "(*) Running Bazel test in devcontainer..."
devcontainer exec --id-label="${ID_LABEL}" /bin/sh -c "set -e && cd \"${REPO_WORKSPACE}\" && bazel test //..."

echo "(*) Bazel build and test completed successfully for ${REPO_NAME}"
