#!/usr/bin/env bash
set -euxo pipefail

IMAGE="s-core-devcontainer"

export DOCKER_BUILDKIT=1

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")
PROJECT_DIR=$(dirname -- "${SCRIPT_DIR}")
ID_LABEL="test-container=${IMAGE}"

devcontainer up \
  --id-label "${ID_LABEL}" \
  --workspace-folder "${PROJECT_DIR}/src/${IMAGE}/" \
  --remove-existing-container

# Run actual test
echo "(*) Running test..."
devcontainer exec --workspace-folder "${PROJECT_DIR}/src/${IMAGE}" --id-label "${ID_LABEL}" \
  /bin/sh -c 'set -e && cd test-project && \
  ./test.sh'
