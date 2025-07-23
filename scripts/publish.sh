#!/usr/bin/env bash
set -euxo pipefail

TAG="${1:-latest}"

if [[ "$TAG" != "latest" ]]; then
    docker tag "ghcr.io/eclipse-score/devcontainer:latest" "ghcr.io/eclipse-score/devcontainer:${TAG}"
fi

docker push "ghcr.io/eclipse-score/devcontainer:${TAG}"
