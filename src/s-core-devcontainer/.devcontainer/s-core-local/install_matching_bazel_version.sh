#!/usr/bin/env bash
set -eo pipefail

. /devcontainer/features/s-core-local/bazel_setup.sh || true

if [ -f .bazelversion ] && [ "$(cat .bazelversion)" != "$INSTALLED_BAZEL_VERSION" ]; then
    # Pre-install the matching Bazel version, setup the bash command completion
    USE_BAZEL_VERSION=$(cat .bazelversion)

    min_bazel_version_for_bash_option="8.4.0"
    bash=""
    if [ "$(printf '%s\n' "$min_bazel_version_for_bash_option" "$USE_BAZEL_VERSION" | sort -V | head -n1)" = "$min_bazel_version_for_bash_option" ]; then
        bash="bash"
    fi

    bazel help completion ${bash} > /tmp/bazel-complete.bash
    sudo mv /tmp/bazel-complete.bash /etc/bash_completion.d/bazel-complete.bash
    echo "INSTALLED_BAZEL_VERSION=$USE_BAZEL_VERSION" | sudo tee /devcontainer/features/s-core-local/bazel_setup.sh
fi
