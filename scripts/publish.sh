#!/usr/bin/env bash
set -euxo pipefail

if [[ "$#" -lt 1 || "$1" != "--arm64" && "$1" != "--amd64" ]]; then
    echo "Error: First parameter must be --arm64 or --amd64."
    exit 1
fi

if [ "$#" -lt 2 ]; then
    echo "Error: At least one label must be provided after the architecture option."
    exit 1
fi

ARCH_OPTION="$1"
shift

ARCH="amd64"
if [[ "$ARCH_OPTION" == "--arm64" ]]; then
    ARCH="arm64"
fi

LABELS=()
for LABEL in "$@"; do
    LABELS+=("${LABEL}")
done

echo "Building all tags (${LABELS[@]}) for architecture: ${ARCH}"
# Prepare image names with tags (each tag includes a label and an architecture)
IMAGES=()
for LABEL in "${LABELS[@]}"; do
    IMAGES+=("--image-name \"ghcr.io/eclipse-score/devcontainer:${LABEL}-${ARCH}\"")
done

# Prepare devcontainer build command
DEVCONTAINER_CALL="devcontainer build --push --workspace-folder src/s-core-devcontainer --cache-from ghcr.io/eclipse-score/devcontainer"

# Append image names to the build command
for IMAGE in "${IMAGES[@]}"; do
    DEVCONTAINER_CALL+=" $IMAGE"
done

# Execute the build and push all tags for the specific architecture
eval "$DEVCONTAINER_CALL --platform linux/${ARCH}"
