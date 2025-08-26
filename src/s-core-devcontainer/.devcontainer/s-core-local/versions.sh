#!/usr/bin/env bash
set -euo pipefail

curl -L "https://github.com/mikefarah/yq/releases/download/v4.47.1/yq_linux_amd64" -o /tmp/yq
echo "0fb28c6680193c41b364193d0c0fc4a03177aecde51cfc04d506b1517158c2fb /tmp/yq" | sha256sum -c - || exit -1
chmod +x /tmp/yq

# Read tool versions and metadata into environment variables
export $(/tmp/yq eval '.. | select((tag == "!!map" or tag == "!!seq") | not) | (path | join("_")) + "=" + .' /devcontainer/features/s-core-local/versions.yaml | awk '!/=$/{print }' | xargs)

# Clean up
rm -f /tmp/yq
