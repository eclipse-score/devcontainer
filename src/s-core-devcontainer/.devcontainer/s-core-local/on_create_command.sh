#!/usr/bin/env bash
set -euo pipefail

# ensure that the Bazel cache directory exists
if [ ! -d /var/cache/bazel ]; then
  echo "Creating /var/cache/bazel directory..."
  # yes, mkdir -p is idempotent, but we want to see the log message
  mkdir -p /var/cache/bazel
fi

# If /var/cache/bazel is not a mountpoint, we assume it is a container-local cache.
# This is the case in codespaces, for example.
# Here, we must ensure that the directory has the correct permissions
# so that Bazel can write to it.
if ! mountpoint -q /var/cache/bazel; then
    echo "/var/cache/bazel is not mounted. Using container-local cache and setting permissions."
    chown -R "$(id -un):$(id -gn)" /var/cache/bazel
fi

# Configure Bazel to use the cache directory
# This way, Bazel can re-use an existing cache on the host machine, if mounted.
# Note that in some scenarios (like codespaces), it is not and hence resides in the container.
echo "startup --output_user_root=/var/cache/bazel" >> ~/.bazelrc

# Configure clangd to remove the -fno-canonical-system-headers flag, which is
# GCC-specific. If not done, there is an annoying error message on the first
# line of every C++ file when being displayed in Visual Studio Code.
mkdir -p ~/.config/clangd
cat > ~/.config/clangd/config.yaml <<EOF
CompileFlags:
  Remove:
    - -fno-canonical-system-headers
EOF
