# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
FROM score-tool-manager-comparison-base:20261031
USER root
# strace is experimental instrumentation, never part of the candidate payload.
RUN apt-get update \
    && apt-get install -y --no-install-recommends strace \
    && rm -rf /var/lib/apt/lists/*
USER probe
