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

runfiles_root="${TEST_SRCDIR}/${TEST_WORKSPACE}"
runner="${runfiles_root}/tools/run-tool"
fake_bin="${TEST_TMPDIR}/bin"
tool_output="${TEST_TMPDIR}/tool.args"
bazel_output="${TEST_TMPDIR}/bazel.args"
mkdir -p "${fake_bin}"

cat > "${fake_bin}/shellcheck" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${FAIL_LOCAL_TOOL:-}" ]]; then
    echo "Simulated local tool error" >&2
    exit "${FAIL_LOCAL_TOOL}"
fi
printf '%s\n' "$@" > "${TOOL_OUTPUT}"
EOF

cat > "${fake_bin}/bazel" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$@" > "${BAZEL_OUTPUT}"
EOF

chmod +x "${fake_bin}/shellcheck" "${fake_bin}/bazel"

assert_lines() {
    local actual_file="$1"
    shift
    local expected_file="${TEST_TMPDIR}/expected-lines"
    printf '%s\n' "$@" > "${expected_file}"
    diff -u "${expected_file}" "${actual_file}"
}

export PATH="${fake_bin}:${PATH}"
export TOOL_OUTPUT="${tool_output}"
export BAZEL_OUTPUT="${bazel_output}"

reset_outputs() {
    rm -f "${tool_output}" "${bazel_output}"
}

# 1. Inside container: executes the container command on PATH directly (untouched).
reset_outputs
export RUN_TOOL_CONTAINER_MODE=container
"${runner}" shellcheck scripts/example.sh
assert_lines "${tool_output}" scripts/example.sh
[[ ! -e "${bazel_output}" ]]

# In container, --strict does not bypass container commands.
reset_outputs
"${runner}" --strict shellcheck scripts/example.sh
assert_lines "${tool_output}" scripts/example.sh
[[ ! -e "${bazel_output}" ]]

# 2. On host: local tool succeeds.
reset_outputs
export RUN_TOOL_CONTAINER_MODE=host
unset FAIL_LOCAL_TOOL || true
"${runner}" shellcheck scripts/example.sh --fix
assert_lines "${tool_output}" scripts/example.sh --fix
[[ ! -e "${bazel_output}" ]]

# 3. On host: local tool fails: preserves exit code and prints message to use --strict.
reset_outputs
export FAIL_LOCAL_TOOL=42
set +e
stderr_output=$("${runner}" shellcheck scripts/example.sh 2>&1 >/dev/null)
status=$?
set -e
[[ "${status}" -eq 42 ]]
echo "${stderr_output}" | grep -q -- "--strict"
echo "${stderr_output}" | grep -q "failed with exit code 42"
[[ ! -e "${bazel_output}" ]]
unset FAIL_LOCAL_TOOL

# 4. On host: --strict flag bypasses local tool and invokes Bazel.
reset_outputs
"${runner}" --strict shellcheck scripts/example.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:shellcheck" \
    "--" \
    "scripts/example.sh"
[[ ! -e "${tool_output}" ]]

# 5. On host or container missing tool: falls back to Bazel.
reset_outputs
"${runner}" missing-tool check.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:missing-tool" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]

# 6. Neither tool nor Bazel is on PATH: exits with 127.
no_bin="${TEST_TMPDIR}/empty-bin"
mkdir -p "${no_bin}"
set +e
no_bazel_output=$(PATH="${no_bin}" /bin/bash "${runner}" missing-tool check.sh 2>&1)
no_bazel_status=$?
set -e
[[ "${no_bazel_status}" -eq 127 ]]
echo "${no_bazel_output}" | grep -q "Could not run 'missing-tool': no container command or Bazel executable is available."
