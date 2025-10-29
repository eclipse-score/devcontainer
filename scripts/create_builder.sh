#!/usr/bin/env bash
set -euxo pipefail

if ! docker buildx inspect multiarch &>/dev/null; then
  docker buildx create --name multiarch --driver docker-container --use
else
  docker buildx use multiarch
fi
