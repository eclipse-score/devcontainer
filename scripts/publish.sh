#!/usr/bin/env bash
set -euxo pipefail

# Define target architectures
ARCHITECTURES=("amd64" "arm64")

# Prepare manifest creation command
MANIFEST_MAIN_CALL="docker manifest create ghcr.io/opajonk/eclipse-score_devcontainer:main"

for ARCH in "${ARCHITECTURES[@]}"; do
    echo "Building for architecture: ${ARCH}"

    # Prepare image names - they should include the architectures and also tags if provided
    IMAGES=("--image-name \"ghcr.io/opajonk/eclipse-score_devcontainer:main-${ARCH}\"")
    # Handle additional tags if provided
    if [ "$#" -gt 0 ]; then
        IMAGES=()
        for arg in "$@"; do
            IMAGES+=("--image-name \"ghcr.io/opajonk/eclipse-score_devcontainer:${arg}-${ARCH}\"")
        done
    fi

    # Prepare devcontainer build command
    DEVCONTAINER_CALL="devcontainer build --push --workspace-folder src/s-core-devcontainer --cache-from ghcr.io/opajonk/eclipse-score_devcontainer"

    # Append image names to the build command
    for IMAGE in "${IMAGES[@]}"; do
        DEVCONTAINER_CALL+=" $IMAGE"
    done

    # Execute the build for the specific architecture
    eval "$DEVCONTAINER_CALL --platform linux/${ARCH}"

    # Append the architecture-specific image to the manifest creation command (those need to be merged into *one* manifest)
    MANIFEST_MAIN_CALL+=" ghcr.io/opajonk/eclipse-score_devcontainer:main-${ARCH}"
done

# Create and push the manifest for 'main' tag
eval "$MANIFEST_MAIN_CALL"
docker manifest push ghcr.io/opajonk/eclipse-score_devcontainer:main

# If additional tags are provided: merge metadata and push those as well
if [ "$#" -gt 0 ]; then
    for arg in "$@"; do
        MANIFEST_TAG_CALL="docker manifest create ghcr.io/opajonk/eclipse-score_devcontainer:${arg}"
        for ARCH in "${ARCHITECTURES[@]}"; do
            MANIFEST_TAG_CALL+=" ghcr.io/opajonk/eclipse-score_devcontainer:${arg}-${ARCH}"
        done
        eval "$MANIFEST_TAG_CALL"
        docker manifest push ghcr.io/opajonk/eclipse-score_devcontainer:${arg}
    done
fi
