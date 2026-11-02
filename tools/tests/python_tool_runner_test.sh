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

# The runfiles tree is the stable dependency root inside Bazel's test sandbox.
runfiles_root="${TEST_SRCDIR}/${TEST_WORKSPACE}"
installer="${runfiles_root}/tools/internal/devcontainer/install.py"
runner="${runfiles_root}/tools/internal/run_python_tool.sh"

fake_uvx="${TEST_TMPDIR}/uvx"
output="${TEST_TMPDIR}/uvx.args"
working_directory="${TEST_TMPDIR}/working-directory"
mkdir -p "${working_directory}"

# A unified diff makes runner-to-uv contract failures directly actionable.
assert_lines() {
    local actual_file="$1"
    shift

    local expected_file="${TEST_TMPDIR}/expected-lines"
    printf '%s\n' "$@" > "${expected_file}"
    diff -u "${expected_file}" "${actual_file}"
}

# A fake uvx executable keeps checks of process boundaries, arguments, and cwd
# network-free.
cat > "${fake_uvx}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "${PWD}" "$@" > "${OUTPUT_FILE}"
exit "${FAKE_UV_EXIT_CODE:-0}"
EOF
chmod +x "${fake_uvx}"

# Resolve the runtime requirement from its owner. This test verifies process
# boundaries without maintaining a second copy of the package-version decision.
catalog_version="$("${installer}" version pre-commit)"
[[ -n "${catalog_version}" ]]

# The Bazel launcher receives an execroot-relative uvx path, then changes to the
# caller's workspace. This catches regressions where that path breaks after cd.
pushd "${TEST_TMPDIR}" > /dev/null
OUTPUT_FILE="${output}" \
    BUILD_WORKING_DIRECTORY="${working_directory}" \
    "${runner}" ./uvx "pre-commit==${catalog_version}" pre-commit run --all-files
popd > /dev/null

assert_lines "${output}" \
    "${working_directory}" \
    "--from" \
    "pre-commit==${catalog_version}" \
    "pre-commit" \
    "run" \
    "--all-files"

# Hook failures must reach Bazel/CI as failures instead of being swallowed by
# the shell boundary after the working-directory change.
set +e
FAKE_UV_EXIT_CODE=37 OUTPUT_FILE="${output}" \
    BUILD_WORKING_DIRECTORY="${working_directory}" \
    "${runner}" "${fake_uvx}" "pre-commit==${catalog_version}" pre-commit run
status=$?
set -e
[[ "${status}" -eq 37 ]]
