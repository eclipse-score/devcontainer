#!/usr/bin/env bash
set -eo pipefail

if [ -f .bazelversion ] && [ "$(cat .bazelversion)" != "$(bazel version | grep 'Build label:' | awk '{print $3}')" ]; then
    # Pre-install the matching Bazel version, setup the bash command completion
    USE_BAZEL_VERSION=$(cat .bazelversion)
    bazel help completion bash > /tmp/bazel-complete.bash
    sudo mv /tmp/bazel-complete.bash /etc/bash_completion.d/bazel-complete.bash
    sudo sed -i '/^USE_BAZEL_VERSION=/c\USE_BAZEL_VERSION=${USE_BAZEL_VERSION}' /etc/profile.d/bazel.sh || true
fi
