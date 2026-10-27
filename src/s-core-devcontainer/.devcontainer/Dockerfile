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

LABEL dev.containers.features="common"

# Refresh the system trust store before anything else downloads over TLS. The
# base image carries the CA bundle from its own build date, and the
# common-utils feature deliberately runs with `upgradePackages: false`, so a
# distrusted CA would otherwise stay trusted for the life of the image.
# Deliberately unpinned: a pinned trust store is a stale trust store.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates --fresh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY tools /usr/local/share/score-tools

RUN userdel -f -r ubuntu
