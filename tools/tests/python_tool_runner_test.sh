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

# One fake executable models both `uvx` execution and `uv tool install`, keeping
# checks of process boundaries, arguments, cwd, and environment network-free.
cat > "${fake_uvx}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
{
    printf '%s\n' "${PWD}"
    printf '%s\n' "$@"
} > "${OUTPUT_FILE}"
if [[ -n "${ENV_OUTPUT:-}" ]]; then
    printf '%s\n%s\n' "${UV_TOOL_BIN_DIR:-}" "${UV_TOOL_DIR:-}" > "${ENV_OUTPUT}"
fi
EOF
chmod +x "${fake_uvx}"

# The explicit assertion verifies the requested release. Subsequent checks use
# the parsed value to keep every expected uv argument aligned with the catalog.
catalog_version="$(python3 "${installer}" version pre-commit)"
[[ "${catalog_version}" = "4.5.1" ]]

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

# Explicit uv directories keep root-owned feature installs independent of
# whichever home directory uv would otherwise infer during image creation.
environment_output="${TEST_TMPDIR}/uvx.env"
OUTPUT_FILE="${output}" ENV_OUTPUT="${environment_output}" \
    python3 "${installer}" install-python pre-commit \
    --uv "${fake_uvx}" --bin-dir /test/bin --tool-dir /test/tools

assert_lines "${output}" \
    "${PWD}" \
    "tool" \
    "install" \
    "--force" \
    "pre-commit==${catalog_version}"
assert_lines "${environment_output}" "/test/bin" "/test/tools"

# Validate all names before invoking uv. Including a valid name first proves an
# error cannot leave behind a partially installed tool set.
rm -f "${output}"
if OUTPUT_FILE="${output}" python3 "${installer}" install-python \
    pre-commit missing-tool \
    --uv "${fake_uvx}" 2> "${TEST_TMPDIR}/unknown.err"; then
    echo "Unknown Python tool unexpectedly succeeded" >&2
    exit 1
fi
grep -qF "Tool 'missing-tool' not found in Python tool catalog" "${TEST_TMPDIR}/unknown.err"
if [[ -e "${output}" ]]; then
    echo "uv was invoked before all requested tools were validated" >&2
    exit 1
fi
