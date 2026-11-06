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

# The cwd wrapper invokes this launcher inside its own runfiles tree without
# exporting RUNFILES_DIR. Recover that tree before loading the runfiles library.
if [[ -z "${RUNFILES_DIR:-}" && "$0" == *.runfiles/* ]]; then
    export RUNFILES_DIR="${0%%.runfiles/*}.runfiles"
fi

# Locate Bazel's runfiles library in both directory and manifest layouts.
runfiles_library="bazel_tools/tools/bash/runfiles/runfiles.bash"
# shellcheck disable=SC1090
source "${RUNFILES_DIR:-/dev/null}/${runfiles_library}" 2>/dev/null ||
    source "$(grep -sm1 "^${runfiles_library} " "${RUNFILES_MANIFEST_FILE:-/dev/null}" | cut -d ' ' -f 2-)" 2>/dev/null ||
    source "$0.runfiles/${runfiles_library}" 2>/dev/null ||
    source "$(grep -sm1 "^${runfiles_library} " "$0.runfiles_manifest" | cut -d ' ' -f 2-)" 2>/dev/null ||
    { echo "Cannot locate Bazel runfiles library" >&2; exit 1; }
set -e

binary="$(rlocation "@BINARY@")"

# The executable and its native libraries remain siblings in the runfiles bundle.
exec "${binary}" "$@"
