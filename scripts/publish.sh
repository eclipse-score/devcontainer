#!/usr/bin/env bash
set -euxo pipefail

if [ "$#" -eq 0 ]; then
    echo "Error: At least one parameter (tag) must be provided."
    exit 1
fi

TAGS=()
for arg in "$@"; do
    TAGS+=("${arg}")
done

# Define target architectures
ARCHITECTURES=("amd64" "arm64")

# Build and push for each architecture, creating all requested tags
for ARCH in "${ARCHITECTURES[@]}"; do
    echo "Building all tags (${TAGS[@]}) for architecture: ${ARCH}"

    # Prepare image names - they should include the architectures and also tags if provided
    IMAGES=()
    # Handle tags if provided
    for TAG in "${TAGS[@]}"; do
        IMAGES+=("--image-name \"ghcr.io/opajonk/eclipse-score_devcontainer:${TAG}-${ARCH}\"")
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

# Create and push the merged multiarch manifest for each tag
for TAG in "${TAGS[@]}"; do
    echo "Merging all architectures (${ARCHITECTURES[@]}) into single tag: ${TAG}"

    MANIFEST_MERGE_CALL="docker buildx imagetools create -t ghcr.io/opajonk/eclipse-score_devcontainer:${TAG}"

    for ARCH in "${ARCHITECTURES[@]}"; do
        MANIFEST_MERGE_CALL+=" ghcr.io/opajonk/eclipse-score_devcontainer:${TAG}-${ARCH}"
    done

    eval "$MANIFEST_MERGE_CALL"
done
