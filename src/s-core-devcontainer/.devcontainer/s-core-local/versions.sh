#!/usr/bin/env bash
set -euo pipefail

ARCHITECTURE=$(dpkg --print-architecture)
VERSION="v4.47.2"

SHA256_FIELD="1bb99e1019e23de33c7e6afc23e93dad72aad6cf2cb03c797f068ea79814ddb0" # Default to amd64
if [ "${ARCHITECTURE}" = "arm64" ]; then
  SHA256_FIELD="05df1f6aed334f223bb3e6a967db259f7185e33650c3b6447625e16fea0ed31f"
fi

curl -L "https://github.com/mikefarah/yq/releases/download/${VERSION}/yq_linux_${ARCHITECTURE}" -o /tmp/yq
echo "${SHA256_FIELD} /tmp/yq" | sha256sum -c - || exit -1
chmod +x /tmp/yq

# Read tool versions and metadata into environment variables
export $(/tmp/yq eval '.. | select((tag == "!!map" or tag == "!!seq") | not) | (path | join("_")) + "=" + .' /devcontainer/features/s-core-local/versions.yaml | awk '!/=$/{print }' | xargs)

# Clean up
rm -f /tmp/yq
