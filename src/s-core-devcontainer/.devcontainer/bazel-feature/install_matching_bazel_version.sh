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
# SPDX-FileCopyrightText: Copyright (c) 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -eo pipefail

. /devcontainer/features/bazel/bazel_setup.sh || true

if [ -f .bazelversion ] && [ "$(cat .bazelversion)" != "${INSTALLED_BAZEL_VERSION}" ]; then
    # Pre-install the matching Bazel version, setup the bash command completion
    USE_BAZEL_VERSION=$(cat .bazelversion)

    min_bazel_version_for_bash_option="8.4.0"
    bash=""
    if [ "$(printf '%s\n' "${min_bazel_version_for_bash_option}" "${USE_BAZEL_VERSION}" | sort -V | head -n1)" = "${min_bazel_version_for_bash_option}" ]; then
        bash="bash"
    fi

    # shellcheck disable=SC2248
    # without quotes is intentional: $bash might be empty and then an empty string is passed to the command, which will fail
    bazel help completion ${bash} > /tmp/bazel-complete.bash
    sudo mv /tmp/bazel-complete.bash /etc/bash_completion.d/bazel-complete.bash
    echo "INSTALLED_BAZEL_VERSION=${USE_BAZEL_VERSION}" | sudo tee /devcontainer/features/bazel/bazel_setup.sh
fi
