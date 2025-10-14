#!/usr/bin/env bash
set -euxo pipefail

devcontainer build --platform linux/arm64 --workspace-folder src/s-core-devcontainer --image-name ghcr.io/eclipse-score/devcontainer --cache-from ghcr.io/eclipse-score/devcontainer
devcontainer build --platform linux/amd64 --workspace-folder src/s-core-devcontainer --image-name ghcr.io/eclipse-score/devcontainer --cache-from ghcr.io/eclipse-score/devcontainer
