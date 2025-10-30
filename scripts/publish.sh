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
ARCHITECTURES=("amd64" "arm64")

# Build and push for each architecture, creating all requested tags
for ARCH in "${ARCHITECTURES[@]}"; do
    echo "Building all tags (${LABELS[@]}) for architecture: ${ARCH}"

    # Prepare image names with tags (each tag includes a label and an architecture)
    IMAGES=()
    for LABEL in "${LABELS[@]}"; do
        IMAGES+=("--image-name \"ghcr.io/opajonk/eclipse-score_devcontainer:${LABEL}-${ARCH}\"")
    done

    # Prepare devcontainer build command
    DEVCONTAINER_CALL="devcontainer build --push --workspace-folder src/s-core-devcontainer --cache-from ghcr.io/opajonk/eclipse-score_devcontainer"

    # Append image names to the build command
    for IMAGE in "${IMAGES[@]}"; do
        DEVCONTAINER_CALL+=" $IMAGE"
    done

    # Execute the build and push all tags for the specific architecture
    eval "$DEVCONTAINER_CALL --platform linux/${ARCH}"
done

# Create and push the merged multiarch manifest for each tag; each tag combines all architecture-specific tags into one tag
for LABEL in "${LABELS[@]}"; do
    echo "Merging all architectures (${ARCHITECTURES[@]}) into single tag: ${LABEL}"

    MANIFEST_MERGE_CALL="docker buildx imagetools create -t ghcr.io/opajonk/eclipse-score_devcontainer:${LABEL}"

    for ARCH in "${ARCHITECTURES[@]}"; do
        MANIFEST_MERGE_CALL+=" ghcr.io/opajonk/eclipse-score_devcontainer:${LABEL}-${ARCH}"
    done

    eval "$MANIFEST_MERGE_CALL"
done
