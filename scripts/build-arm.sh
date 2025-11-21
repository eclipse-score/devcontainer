#!/usr/bin/env bash
set -euxo pipefail

if [ "$#" -eq 0 ]; then
    echo "Error: At least one parameter (label) must be provided."
    exit 1
fi

LABELS=()
for LABEL in "$@"; do
    LABELS+=("${LABEL}")
done

# Define target architectures
ARCHITECTURES=("arm64")

# Build for each architecture, creating all requested tags
for ARCH in "${ARCHITECTURES[@]}"; do
    echo "Building all labels (${LABELS[@]}) for architecture: ${ARCH}"

    # Prepare image names with tags (each tag includes a label and an architecture)
    IMAGES=()
    for LABEL in "${LABELS[@]}"; do
        IMAGES+=("--image-name \"ghcr.io/opajonk/eclipse-score_devcontainer:${LABEL}-${ARCH}\"")
    done

    # Prepare devcontainer build command
    DEVCONTAINER_CALL="devcontainer build --workspace-folder src/s-core-devcontainer --cache-from ghcr.io/opajonk/eclipse-score_devcontainer"

    # Append image names to the build command
    for IMAGE in "${IMAGES[@]}"; do
        DEVCONTAINER_CALL+=" $IMAGE"
    done

    # Execute the build for the specific architecture
    eval "$DEVCONTAINER_CALL --platform linux/${ARCH}"
done
