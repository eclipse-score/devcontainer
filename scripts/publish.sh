#!/usr/bin/env bash
set -euxo pipefail

TAG="${1:-latest}"

devcontainer build --push --platform linux/aarch64,linux/amd64 --workspace-folder src/s-core-devcontainer --image-name "ghcr.io/eclipse-score/devcontainer:${TAG}" --cache-from ghcr.io/eclipse-score/devcontainer
