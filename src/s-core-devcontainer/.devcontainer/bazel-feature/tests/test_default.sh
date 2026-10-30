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
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -euo pipefail

installer=/usr/local/share/score-tools/internal/devcontainer/install.py
. /usr/local/share/score-tools/internal/devcontainer/load_feature_versions.sh
check "verify selected Bazel tooling" "${installer}" verify-environment bazel-feature

# The image preinstall version is separate from a consuming workspace's choice.
if "${installer}" selected bazel-feature bazel; then
    export USE_BAZEL_VERSION=${bazel_version}
    check "validate preinstalled Bazel" bash -c "bazel version | grep '${bazel_version}'"
    unset USE_BAZEL_VERSION
fi
if "${installer}" selected bazel-feature bazel_compile_commands; then
    check "validate compilation database helper" bash -c "bazel-compile-commands --version 2>&1 | grep '${bazel_compile_commands_version}'"
fi
