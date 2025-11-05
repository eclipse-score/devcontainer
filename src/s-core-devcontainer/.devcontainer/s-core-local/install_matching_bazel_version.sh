#!/usr/bin/env bash
set -eo pipefail

. /etc/profile.d/bazel.sh || true

if [ -f .bazelversion ] && [ "$(cat .bazelversion)" != "$USE_BAZEL_VERSION" ]; then
    # Pre-install the matching Bazel version, setup the bash command completion
    USE_BAZEL_VERSION=$(cat .bazelversion)
    bazel help completion > /tmp/bazel-complete.bash
    sudo mv /tmp/bazel-complete.bash /etc/bash_completion.d/bazel-complete.bash
    echo "export USE_BAZEL_VERSION=$USE_BAZEL_VERSION" | sudo tee /etc/profile.d/bazel.sh
fi
