#!/usr/bin/env bash
set -euo pipefail

# ensure that the Bazel cache directory has the correct permissions
sudo chown -R "$(id -un):$(id -gn)" /var/cache/bazel
