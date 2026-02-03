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
  echo "Bazel Cache: Configuring Bazel to use /var/cache/bazel as cache (= output user root)..."
  echo "startup --output_user_root=/var/cache/bazel" >> ~/.bazelrc
  echo "Bazel Cache: Configuring Bazel disk cache to be in /var/cache/bazel/diskcache..."
  echo "common --disk_cache=/var/cache/bazel/diskcache" >> ~/.bazelrc
else
  echo "Bazel Cache: Configuring Bazel disk cache to be in ~/.cache/bazel/_disk_cache..."
  # Assuming the default location for the output user root folder is used
  # Put disk cache folder within output user root folder
  echo "common --disk_cache=~/.cache/bazel/_disk_cache" >> ~/.bazelrc
fi
echo "Bazel Cache: Configuring Bazel disk cache retention time (60 days)..."
echo "common --experimental_disk_cache_gc_max_age=60d" >> ~/.bazelrc
echo "Bazel Cache: Configuring Bazel disk cache max size (50 GB)..."
echo "common --experimental_disk_cache_gc_max_size=50G" >> ~/.bazelrc
