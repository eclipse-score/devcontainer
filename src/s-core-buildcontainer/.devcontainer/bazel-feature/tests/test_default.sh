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

set -euo pipefail

# Read tool versions + metadata into environment variables
. /devcontainer/features/s-core-build/versions.sh /devcontainer/features/bazel/versions.yaml

# Bazel-related tools
## This is the bazel version preinstalled in the devcontainer.
## A solid test would disable the network interface first to prevent a different version from being downloaded,
## but that requires CAP_NET_ADMIN, which is not yet added.
export USE_BAZEL_VERSION=${bazel_version}
check "validate bazelisk is working and has the correct version" bash -c "bazelisk version | grep '${bazelisk_version}'"
check "validate bazel is working and has the correct version" bash -c "bazel version | grep '${bazel_version}'"
unset USE_BAZEL_VERSION

check "validate buildifier is working and has the correct version" bash -c "buildifier --version | grep '${buildifier_version}'"
check "validate starpls is working and has the correct version" bash -c "starpls version | grep '${starpls_version}'"
check "validate bazel-compile-commands is working and has the correct version" bash -c "bazel-compile-commands --version 2>&1 | grep '${bazel_compile_commands_version}'"
