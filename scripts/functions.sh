#!/bin/bash

set_dockerfile_name() {
    DEVCONTAINER_DOCKERFILE_NAME="Dockerfile"

    # Check if proxies are configured in the environment
    set +u
    if [ -n "${HTTP_PROXY}${HTTPS_PROXY}${http_proxy}${https_proxy}${NO_PROXY}${no_proxy}" ]; then
        DEVCONTAINER_DOCKERFILE_NAME="Dockerfile-with-proxy-vars"
        echo "Proxy environment detected."
    fi
    set -u

    export DEVCONTAINER_DOCKERFILE_NAME
    echo "Using Dockerfile: ${DEVCONTAINER_DOCKERFILE_NAME}"
}
