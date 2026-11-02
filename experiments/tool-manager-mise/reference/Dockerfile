# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# The shared Ubuntu base is a tooling-layer fixture, not the outer devcontainer.
FROM score-tool-manager-comparison-base:20261031
USER root
ARG PROFILE
COPY . /release/
RUN bash /release/install.sh / "${PROFILE}" \
    && mkdir -p /home/score /workspace \
    && cp /release/.bazelversion /workspace/.bazelversion \
    && touch /workspace/MODULE.bazel \
    && chown -R 12345:12345 /home/score /workspace
ENV HOME=/home/score
ENV BAZELISK_HOME=/home/score/.cache/bazelisk
ENV PATH=/usr/local/bin:/usr/bin:/bin
USER 12345:12345
WORKDIR /workspace
# Bazelisk is a downloader, so prepare the selected Bazel and embedded JDK online
# as the runtime user. The sole Bazel version owner remains .bazelversion.
RUN bazelisk --version
