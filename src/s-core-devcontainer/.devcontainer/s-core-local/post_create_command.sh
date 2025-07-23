#!/usr/bin/env bash
set -euo pipefail

# Configure Bazel to use the cache directory that is mounted from the host
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
