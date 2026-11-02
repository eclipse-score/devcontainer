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

FROM buildpack-deps:noble-curl

# Proxy arguments for build-time network access
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG http_proxy=""
ARG https_proxy=""
ARG NO_PROXY=""
ARG no_proxy=""

# Set proxy environment variables for the build process
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV http_proxy=${http_proxy}
ENV https_proxy=${https_proxy}
ENV NO_PROXY=${NO_PROXY}
ENV no_proxy=${no_proxy}

LABEL dev.containers.features="common"

# Refresh the system trust store before anything else downloads over TLS. The
# base image carries the CA bundle from its own build date, and the
# common-utils feature deliberately runs with `upgradePackages: false`, so a
# distrusted CA would otherwise stay trusted for the life of the image.
# Deliberately unpinned: a pinned trust store is a stale trust store.
# The owner-driven tool bootstrap below is Python-based and runs before
# Dev Container features can install their runtime providers. Use distro APT
# for this bootstrap interpreter; tool versions remain in their existing owners.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates python3 \
    && update-ca-certificates --fresh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY tools /usr/local/share/score-tools

# Provision the current published owners during every image build. Aqua and uv
# are build-time installers; only their direct selected tools remain in the image.
ARG TARGETARCH
COPY tools/owners/aqua/aqua.yaml /tmp/score-aqua-owner/aqua.yaml
COPY tools/owners/aqua/aqua-policy.yaml /tmp/score-aqua-owner/aqua-policy.yaml
COPY tools/owners/aqua/aqua-bootstrap.toml /tmp/score-aqua-owner/aqua-bootstrap.toml
COPY tools/owners/aqua/aqua-checksums.json /tmp/score-aqua-owner/aqua-checksums.json
COPY tools/owners/aqua/starpls-registry.yaml /tmp/score-aqua-owner/starpls-registry.yaml
COPY tools/owners/aqua/apm-registry.yaml /tmp/score-aqua-owner/apm-registry.yaml
COPY tools/owners/aqua/pyproject.toml /tmp/score-aqua-owner/pyproject.toml
RUN SCORE_AQUA_PLATFORM="linux/${TARGETARCH}" \
    /usr/local/share/score-tools/internal/devcontainer/provision_image_tools.sh \
    /tmp/score-aqua-owner /opt/score-tools \
    && rm -rf /tmp/score-aqua-owner

ENV PATH="/opt/score-tools/bin:${PATH}"

# Unset proxy variables for all login shells
COPY src/s-core-devcontainer/.devcontainer/unset-proxy.sh /etc/bash_completion.d/unset-proxy.sh

RUN userdel -f -r ubuntu
