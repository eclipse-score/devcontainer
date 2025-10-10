#!/usr/bin/env bash
set -euxo pipefail

docker buildx create --name multiarch --driver docker-container --use
