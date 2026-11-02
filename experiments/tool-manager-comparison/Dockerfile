# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
FROM ubuntu:24.04
# Shared test infrastructure, not a proposed production base or tool selection.
# Candidate CLIs must be provisioned independently; this base has no Ruff,
# pre-commit, candidate manager, or uv installation to mask a missing tool.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git python3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 12345 --create-home probe
USER probe
WORKDIR /home/probe
