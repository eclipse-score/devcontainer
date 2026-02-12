#!/usr/bin/env bash

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

set -euxo pipefail

if [ "$#" -eq 0 ]; then
    echo "Error: At least one parameter (label) must be provided."
    exit 1
fi

LABELS=()
for LABEL in "$@"; do
    LABELS+=("${LABEL}")
done

# Define target architectures
ARCHITECTURES=("amd64" "arm64")

# Pull all architecture-specific images for each label
for LABEL in "${LABELS[@]}"; do
    for ARCH in "${ARCHITECTURES[@]}"; do
        docker pull --platform "linux/${ARCH}" "ghcr.io/eclipse-score/devcontainer:${LABEL}-${ARCH}"
    done
done

# Create and push the merged multiarch manifest for each tag; each tag combines all architecture-specific tags into one tag
for LABEL in "${LABELS[@]}"; do
    echo "Merging all architectures (" "${ARCHITECTURES[@]}" ") into single tag: ${LABEL}"

    MANIFEST_MERGE_CALL="docker buildx imagetools create -t ghcr.io/eclipse-score/devcontainer:${LABEL}"

    for ARCH in "${ARCHITECTURES[@]}"; do
        MANIFEST_MERGE_CALL+=" ghcr.io/eclipse-score/devcontainer:${LABEL}-${ARCH}"
    done

    eval "${MANIFEST_MERGE_CALL}"
done
