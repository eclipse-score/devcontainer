#!/usr/bin/env bash
set -euo pipefail

# In some scenarios (like CodeSpaces), apparently not all (or even any?)
# bind mounts to the host are done and /var/cache/bazel does not exist.
# See devcontainer-feature.json, where this mount is defined.
# Hence, if /var/cache/bazel exists, it was mounted from the host,
# and we configure Bazel to use /var/cache/bazel as cache.
# This way, Bazel re-uses a bind-mounted cache from the host machine, while
# still using the default cache (${HOME}/.cache/bazel) if no such cache exists.
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
