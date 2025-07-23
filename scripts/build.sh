#!/usr/bin/env bash
set -euxo pipefail

devcontainer build --workspace-folder src/s-core-devcontainer --image-name ghcr.io/eclipse-score/devcontainer:latest --cache-from ghcr.io/eclipse-score/devcontainer
