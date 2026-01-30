#!/usr/bin/env bash
set -euxo pipefail

# Function to check if builder has correct proxy configuration
check_proxy_config() {
  local builder_info
  builder_info=$(docker buildx inspect multiarch 2>/dev/null || echo "")

  # Check if HTTP_PROXY is set in environment but not in builder
  if [ -n "${HTTP_PROXY:-}" ]; then
    if ! echo "${builder_info}" | grep -q "HTTP_PROXY=${HTTP_PROXY}"; then
      return 1
    fi
  fi

  # Check if HTTPS_PROXY is set in environment but not in builder
  if [ -n "${HTTPS_PROXY:-}" ]; then
    if ! echo "${builder_info}" | grep -q "HTTPS_PROXY=${HTTPS_PROXY}"; then
      return 1
    fi
  fi

  return 0
}

# Check if builder exists and has correct proxy configuration
if docker buildx inspect multiarch &>/dev/null; then
  # shellcheck disable=SC2310
  # it is an optional rule, enabled via --enable all
  if ! check_proxy_config; then
    echo "Builder 'multiarch' exists but has incorrect proxy configuration. Recreating..."
    docker buildx rm multiarch
  else
    echo "Builder 'multiarch' already exists with correct configuration."
    docker buildx use multiarch
    exit 0
  fi
fi

# Create BuildKit configuration file with proxy settings
BUILDKIT_CONFIG=""
if [ -n "${HTTP_PROXY:-}" ] || [ -n "${HTTPS_PROXY:-}" ]; then
  BUILDKIT_CONFIG="${HOME}/.config/buildkit/buildkitd.toml"
  mkdir -p "$(dirname "${BUILDKIT_CONFIG}")"
  cat > "${BUILDKIT_CONFIG}" <<EOF
[worker.oci]
  enabled = true

[worker.containerd]
  enabled = false

# Default build arg values for all builds (includes proxy settings)
[worker.oci.proxy]
  http = "${HTTP_PROXY:-}"
  https = "${HTTPS_PROXY:-}"
  noProxy = "${NO_PROXY:-}"
EOF
fi

# Build driver options for proxy configuration
DRIVER_OPTS=()

if [ -n "${HTTP_PROXY:-}" ]; then
  DRIVER_OPTS+=("--driver-opt" "env.HTTP_PROXY=${HTTP_PROXY}")
fi

if [ -n "${HTTPS_PROXY:-}" ]; then
  DRIVER_OPTS+=("--driver-opt" "env.HTTPS_PROXY=${HTTPS_PROXY}")
fi

if [ -n "${NO_PROXY:-}" ]; then
  DRIVER_OPTS+=("--driver-opt" "env.NO_PROXY=${NO_PROXY}")
fi

# Add network mode to use host DNS resolution
DRIVER_OPTS+=("--driver-opt" "network=host")

# Add BuildKit config file if proxy is configured
if [ -n "${BUILDKIT_CONFIG}" ]; then
  DRIVER_OPTS+=("--config" "${BUILDKIT_CONFIG}")
fi

# Create builder with driver options
docker buildx create --name multiarch --driver docker-container "${DRIVER_OPTS[@]}" --use
