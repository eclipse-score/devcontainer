#!/usr/bin/env bash
set -eo pipefail

if [ -f .bazelversion ] && [ "$(cat .bazelversion)" != "$(dpkg --list | grep 'ii  bazel   ' | awk '{print $3}')" ]; then
    sudo apt-get update && sudo apt-get install -y --allow-downgrades bazel=$(cat .bazelversion)
fi
