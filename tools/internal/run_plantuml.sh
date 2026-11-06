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

set -uo pipefail

# Locate Bazel's runfiles library in both directory and manifest layouts.
runfiles_library="bazel_tools/tools/bash/runfiles/runfiles.bash"
# shellcheck disable=SC1090
source "${RUNFILES_DIR:-/dev/null}/${runfiles_library}" 2>/dev/null ||
    source "$(grep -sm1 "^${runfiles_library} " "${RUNFILES_MANIFEST_FILE:-/dev/null}" | cut -d ' ' -f 2-)" 2>/dev/null ||
    source "$0.runfiles/${runfiles_library}" 2>/dev/null ||
    source "$(grep -sm1 "^${runfiles_library} " "$0.runfiles_manifest" | cut -d ' ' -f 2-)" 2>/dev/null ||
    { echo "Cannot locate Bazel runfiles library" >&2; exit 1; }
set -e

mode="@MODE@"
binary="$(rlocation "@BINARY@")"

if [[ "${mode}" == "cwd" && -n "${BUILD_WORKING_DIRECTORY:-}" ]]; then
    cd "${BUILD_WORKING_DIRECTORY}"
fi

# The executable and its native libraries remain siblings in the runfiles bundle.
exec "${binary}" "$@"
