#!/usr/bin/env bash
set -euxo pipefail

IMAGES=("--image-name \"ghcr.io/eclipse-score/devcontainer:main\"")
if [ "$#" -gt 0 ]; then
    IMAGES=()
    for arg in "$@"; do
        IMAGES+=("--image-name \"ghcr.io/eclipse-score/devcontainer:${arg}\"")
    done
fi

DEVCONTAINER_CALL="devcontainer build --push --workspace-folder src/s-core-devcontainer --cache-from ghcr.io/eclipse-score/devcontainer"

for IMAGE in "${IMAGES[@]}"; do
    DEVCONTAINER_CALL+=" $IMAGE"
done

eval "$DEVCONTAINER_CALL --platform linux/amd64"
eval "$DEVCONTAINER_CALL --platform linux/arm64"
