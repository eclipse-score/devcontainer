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

# Bazel supplies the pinned uvx binary and catalog metadata as fixed arguments.
# Keeping this launcher in shell avoids making Python a host prerequisite.
# Strict mode prevents missing catalog arguments or failed directory changes
# from continuing as a misleading tool invocation.
set -euo pipefail

# This is an internal contract check: the first three arguments are generated
# by python_tool.bzl, while every remaining argument belongs to the user.
if [[ "$#" -lt 3 ]]; then
    echo "Usage: $0 <uvx> <package==version> <entrypoint> [args...]" >&2
    exit 2
fi

uvx="$1"
requirement="$2"
entrypoint="$3"
shift 3

# $(location) can be relative to Bazel's execution root. Make it stable before
# changing to the user's workspace, where CLI tools expect to discover config.
if [[ "${uvx}" != /* ]]; then
    uvx="${PWD}/${uvx}"
fi

# `bazel run` sets BUILD_WORKING_DIRECTORY to the caller's cwd. The workspace
# value is a conservative fallback for wrappers that only expose the root.
working_directory="${BUILD_WORKING_DIRECTORY:-${BUILD_WORKSPACE_DIRECTORY:-}}"
if [[ -n "${working_directory}" ]]; then
    cd "${working_directory}"
fi

# Replace the launcher process so uvx forwards signals and its exit status
# directly to Bazel, pre-commit, and interactive callers.
exec "${uvx}" --from "${requirement}" "${entrypoint}" "$@"
