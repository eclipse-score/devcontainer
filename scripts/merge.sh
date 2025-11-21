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
ARCHITECTURES=("amd64", "arm64")

# Create and push the merged multiarch manifest for each tag; each tag combines all architecture-specific tags into one tag
for LABEL in "${LABELS[@]}"; do
    echo "Merging all architectures (${ARCHITECTURES[@]}) into single tag: ${LABEL}"

    MANIFEST_MERGE_CALL="docker buildx imagetools create -t ghcr.io/opajonk/eclipse-score_devcontainer:${LABEL}"

    for ARCH in "${ARCHITECTURES[@]}"; do
        MANIFEST_MERGE_CALL+=" ghcr.io/opajonk/eclipse-score_devcontainer:${LABEL}-${ARCH}"
    done

    eval "$MANIFEST_MERGE_CALL"
done
