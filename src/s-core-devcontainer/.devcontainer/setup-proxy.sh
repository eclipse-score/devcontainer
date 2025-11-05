#!/bin/bash

# Post-create script to configure Docker daemon with proxy settings
# This script will run automatically when the devcontainer is created

set -e

echo "🔧 Setting up Docker daemon with proxy configuration..."

# Check if any proxy variables are set
if [[ -n "${HTTP_PROXY:-}" || -n "${HTTPS_PROXY:-}" || -n "${http_proxy:-}" || -n "${https_proxy:-}" ]]; then
    echo "📡 Proxy environment detected, configuring Docker daemon..."

    # Create systemd service directory for Docker
    sudo mkdir -p /etc/systemd/system/docker.service.d

    # Create Docker daemon proxy configuration
    sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null << EOF
[Service]
Environment="HTTP_PROXY=${HTTP_PROXY:-}"
Environment="HTTPS_PROXY=${HTTPS_PROXY:-}"
Environment="http_proxy=${http_proxy:-}"
Environment="https_proxy=${https_proxy:-}"
Environment="NO_PROXY=${NO_PROXY:-localhost,127.0.0.1,docker-registry.example.com,.corp}"
Environment="no_proxy=${no_proxy:-localhost,127.0.0.1,docker-registry.example.com,.corp}"
EOF

    # Create Docker daemon configuration
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json > /dev/null << EOF
{
  "registry-mirrors": [],
  "insecure-registries": [],
  "debug": false,
  "experimental": false,
  "dns": ["8.8.8.8", "1.1.1.1"],
  "dns-search": [],
  "dns-opts": []
}
EOF

    # Create Docker client proxy configuration for the user
    mkdir -p ~/.docker
    tee ~/.docker/config.json > /dev/null << EOF
{
  "proxies": {
    "default": {
      "httpProxy": "${HTTP_PROXY:-}",
      "httpsProxy": "${HTTPS_PROXY:-}",
      "noProxy": "${NO_PROXY:-localhost,127.0.0.1}"
    }
  }
}
EOF

    # Function to restart Docker daemon with proxy settings
    restart_docker_with_proxy() {
        echo "🔄 Restarting Docker daemon with proxy settings..."

        # Kill existing dockerd if running
        if pgrep dockerd > /dev/null; then
            echo "Stopping existing Docker daemon..."
            sudo pkill dockerd || true
            sleep 3
        fi

        # Start Docker daemon with proxy environment variables
        echo "Starting Docker daemon with proxy configuration..."
        sudo HTTP_PROXY="${HTTP_PROXY:-}" HTTPS_PROXY="${HTTPS_PROXY:-}" \
             http_proxy="${http_proxy:-}" https_proxy="${https_proxy:-}" \
             NO_PROXY="${NO_PROXY:-}" no_proxy="${no_proxy:-}" \
             dockerd --config-file /etc/docker/daemon.json > /dev/null 2>&1 &

        # Wait for Docker to start
        echo "Waiting for Docker daemon to start..."
        for i in {1..30}; do
            if docker info > /dev/null 2>&1; then
                echo "✅ Docker daemon started successfully"
                break
            fi
            echo "Waiting for Docker daemon... ($i/30)"
            sleep 2
        done

        # Verify Docker is working
        if ! docker info > /dev/null 2>&1; then
            echo "❌ Failed to start Docker daemon, trying alternative approach..."

            # Try without config file
            sudo pkill dockerd > /dev/null 2>&1 || true
            sleep 2
            sudo HTTP_PROXY="${HTTP_PROXY:-}" HTTPS_PROXY="${HTTPS_PROXY:-}" \
                 http_proxy="${http_proxy:-}" https_proxy="${https_proxy:-}" \
                 NO_PROXY="${NO_PROXY:-}" no_proxy="${no_proxy:-}" \
                 dockerd > /dev/null 2>&1 &

            sleep 5
            if ! docker info > /dev/null 2>&1; then
                echo "❌ Failed to start Docker daemon"
                return 1
            fi
        fi

        # Verify proxy settings are applied
        if docker info | grep -q "HTTP Proxy\|HTTPS Proxy"; then
            echo "✅ Proxy settings successfully applied to Docker daemon"
        else
            echo "⚠️  Proxy settings may not be fully applied, but Docker is working"
        fi
    }

    # Restart Docker with proxy settings
    restart_docker_with_proxy

    # Configure BuildKit with proxy
    echo "🏗️  Configuring BuildKit with proxy settings..."

    # Remove existing multiarch builder if it exists
    docker buildx rm multiarch 2>/dev/null || true

    # Prepare buildx command with proxy options
    BUILDX_CMD="docker buildx create --name multiarch --driver docker-container --driver-opt network=host"

    # Add proxy environment variables only if they are set and non-empty
    if [[ -n "${HTTP_PROXY:-}" ]]; then
        BUILDX_CMD="$BUILDX_CMD --driver-opt env.HTTP_PROXY=${HTTP_PROXY}"
    fi

    if [[ -n "${HTTPS_PROXY:-}" ]]; then
        BUILDX_CMD="$BUILDX_CMD --driver-opt env.HTTPS_PROXY=${HTTPS_PROXY}"
    fi

    if [[ -n "${http_proxy:-}" ]]; then
        BUILDX_CMD="$BUILDX_CMD --driver-opt env.http_proxy=${http_proxy}"
    fi

    if [[ -n "${https_proxy:-}" ]]; then
        BUILDX_CMD="$BUILDX_CMD --driver-opt env.https_proxy=${https_proxy}"
    fi

    # Add NO_PROXY only if set
    if [[ -n "${NO_PROXY:-}" ]]; then
        BUILDX_CMD="$BUILDX_CMD --driver-opt env.NO_PROXY=${NO_PROXY}"
    fi

    if [[ -n "${no_proxy:-}" ]]; then
        BUILDX_CMD="$BUILDX_CMD --driver-opt env.no_proxy=${no_proxy}"
    fi

    # Execute the buildx command
    eval $BUILDX_CMD

    # Use the new builder
    docker buildx use multiarch

    # Bootstrap the builder
    echo "🚀 Bootstrapping BuildKit instance..."
    docker buildx inspect --bootstrap

    echo "✅ Docker and BuildKit configured with proxy settings"

else
    echo "🌐 No proxy environment detected, using default Docker configuration..."

    # Start Docker daemon if not running
    if ! pgrep dockerd > /dev/null; then
        echo "🔄 Starting Docker daemon..."
        sudo dockerd > /dev/null 2>&1 &

        # Wait for Docker to start
        for i in {1..30}; do
            if docker info > /dev/null 2>&1; then
                echo "✅ Docker daemon started successfully"
                break
            fi
            echo "Waiting for Docker daemon... ($i/30)"
            sleep 2
        done

        if ! docker info > /dev/null 2>&1; then
            echo "❌ Failed to start Docker daemon"
            exit 1
        fi
    fi

    # Ensure basic Docker configuration exists
    sudo mkdir -p /etc/docker
    if [[ ! -f /etc/docker/daemon.json ]]; then
        sudo tee /etc/docker/daemon.json > /dev/null << EOF
{
  "registry-mirrors": [],
  "insecure-registries": [],
  "debug": false,
  "experimental": false
}
EOF
    fi

    # Set up basic BuildKit if not already configured
    if ! docker buildx ls | grep -q multiarch; then
        echo "🏗️  Setting up default BuildKit configuration..."
        docker buildx create --name multiarch --driver docker-container --use
        docker buildx inspect --bootstrap
    fi

    echo "✅ Default Docker configuration applied"
fi

# Verify everything is working
echo "🧪 Testing Docker functionality..."
if docker run --rm hello-world > /dev/null 2>&1; then
    echo "✅ Docker is working correctly"
else
    echo "❌ Docker test failed"
    exit 1
fi

echo "🎉 Docker setup completed successfully!"
