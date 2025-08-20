#!/usr/bin/env bash
set -euo pipefail

# Enable persistent Bazel cache
#
# Usually, a volume is mounted to /var/cache/bazel (see
# devcontainer-feature.json). This shall be used as Bazel cache, which is then
# preserved across container re-starts. Since the volume has a fixed
# name ("eclipse-s-core-bazel-cache"), it is even used across all Eclipse
# S-CORE DevContainer instances.
if [ -d /var/cache/bazel ]; then
  echo "Bazel Cache: /var/cache/bazel exists. Checking ownership and configuring Bazel to use it as cache..."
  current_owner_group=$(stat -c "%U:%G" /var/cache/bazel)
  current_user_group="$(id -un):$(id -gn)"
  if [ "${current_owner_group}" = "${current_user_group}" ]; then
    echo "Bazel Cache: /var/cache/bazel is already owned by ${current_user_group}. "
  else
    echo "Bazel Cache: /var/cache/bazel is not owned by ${current_owner_group}. Setting ownership (this may take a few seconds) ..."
    sudo chown -R "${current_user_group}" /var/cache/bazel
  fi
  echo "Bazel Cache: Configuring Bazel to use /var/cache/bazel as cache..."
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
