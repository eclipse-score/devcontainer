#!/usr/bin/env bash
set -euo pipefail

# If /var/cache/bazel exists, it was mounted from the host (see devcontainer-feature.json).
# Hence, we configure Bazel to use this cache directory instead of the default cache (${HOME}/.cache/bazel).
# This way, Bazel can re-use an existing cache on the host machine.
# Note that in some scenarios (like codespaces), this is not the case and hence the cache stays in the container.
if [ -d /var/cache/bazel ]; then
  echo "Configuring Bazel to use /var/cache/bazel as cache..."
  echo "startup --output_user_root=/var/cache/bazel" >> ~/.bazelrc
fi

# Configure clangd to remove the -fno-canonical-system-headers flag, which is
# GCC-specific. If not done, there is an annoying error message on the first
# line of every C++ file when being displayed in Visual Studio Code.
mkdir -p ~/.config/clangd
cat > ~/.config/clangd/config.yaml <<EOF
CompileFlags:
  Remove:
    - -fno-canonical-system-headers
EOF
