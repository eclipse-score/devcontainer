# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
FROM score-tool-manager-comparison-base:20261031
USER root
ARG PROFILE
ARG BAZEL_VERSION
COPY runtime/${PROFILE}/ /opt/score-tools/
COPY run-tool /usr/local/bin/run-tool
COPY .bazelversion /workspace/.bazelversion
COPY image-check.py /probe/image-check.py
COPY ${PROFILE}.expected.json /probe/expected.json
ENV PATH=/opt/score-tools/bin:/usr/local/bin:/usr/bin:/bin \
    HOME=/home/probe \
    PRE_COMMIT_HOME=/home/probe/pre-commit \
    BAZELISK_HOME=/opt/score-bazelisk-cache \
    USE_BAZEL_VERSION=${BAZEL_VERSION}
RUN mkdir -p /home/probe /opt/score-bazelisk-cache && \
    chown -R 12345:12345 /home/probe /opt/score-bazelisk-cache
USER 12345:12345
WORKDIR /workspace
# Resolve the Bazel selected by the existing .bazelversion online during build.
# Its actual binary is copied into this image layer, not bind-mounted at runtime.
RUN bazelisk version
CMD ["python3", "/probe/image-check.py", "/probe/expected.json", "/usr/local/bin/run-tool"]
