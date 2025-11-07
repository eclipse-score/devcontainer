#!/usr/bin/env bash
set -eo pipefail

. /devcontainer/features/s-core-local/bazel_setup.sh || true

if [ -f .bazelversion ] && [ "$(cat .bazelversion)" != "$INSTALLED_BAZEL_VERSION" ]; then
    # Pre-install the matching Bazel version, setup the bash command completion
    USE_BAZEL_VERSION=$(cat .bazelversion)
    bazel help completion > /tmp/bazel-complete.bash
    sudo mv /tmp/bazel-complete.bash /etc/bash_completion.d/bazel-complete.bash
    echo "export INSTALLED_BAZEL_VERSION=$USE_BAZEL_VERSION" | sudo tee /devcontainer/features/s-core-local/bazel_setup.sh
fi
