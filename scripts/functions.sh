#!/bin/bash

# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

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
