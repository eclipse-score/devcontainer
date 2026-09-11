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
version_args_output="${TEST_TMPDIR}/version.args"
bazel_output="${TEST_TMPDIR}/bazel.args"
mkdir -p "${fake_bin}"

cat > "${fake_bin}/shellcheck" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$#" -eq 1 && "${INVALID_VERSION_ARGS:-}" == *"|$1|"* ]]; then
    printf '%s\n' "$1" >> "${VERSION_ARGS_OUTPUT}"
    exit 2
fi
if [[ "$#" -eq 1 && "$1" == "${SUCCESS_VERSION_ARG}" ]]; then
    printf '%s\n' "$1" >> "${VERSION_ARGS_OUTPUT}"
    printf 'ShellCheck - %s\n' "${FAKE_VERSION}"
    exit 0
fi
printf '%s\n' "$@" > "${TOOL_OUTPUT}"
EOF

cat > "${fake_bin}/bazel" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$@" > "${BAZEL_OUTPUT}"
EOF

cat > "${fake_bin}/unknown-tool" <<'EOF'
#!/usr/bin/env bash
printf 'Unknown Tool 1.0.0\n'
EOF
chmod +x "${fake_bin}/shellcheck" "${fake_bin}/bazel" "${fake_bin}/unknown-tool"

assert_lines() {
    local actual_file="$1"
    shift
    local expected_file="${TEST_TMPDIR}/expected-lines"
    printf '%s\n' "$@" > "${expected_file}"
    diff -u "${expected_file}" "${actual_file}"
}

export PATH="${fake_bin}:${PATH}"
export TOOL_OUTPUT="${tool_output}"
export VERSION_ARGS_OUTPUT="${version_args_output}"
export BAZEL_OUTPUT="${bazel_output}"
export INVALID_VERSION_ARGS="|-v|-version|"
export SUCCESS_VERSION_ARG="--version"

# A tool may reject -v and -version; the runner must continue to --version.
export FAKE_VERSION="0.10.0"
"${runner}" shellcheck --help
assert_lines "${version_args_output}" -v -version --version
assert_lines "${tool_output}" --help
[[ ! -e "${bazel_output}" ]]

# When no version flag returns a parseable version, installed_version returns 1
# and the runner must fall back to Bazel.
rm -f "${tool_output}" "${version_args_output}" "${bazel_output}"
export INVALID_VERSION_ARGS="|-v|-version|--version|"
"${runner}" shellcheck check.sh
assert_lines "${version_args_output}" -v -version --version
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:shellcheck" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]

# An installed tool absent from the catalog must also use the Bazel target.
rm -f "${tool_output}" "${version_args_output}" "${bazel_output}"
"${runner}" unknown-tool check.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:unknown-tool" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]

# Strict mode always uses the Bazel target.
rm -f "${tool_output}" "${version_args_output}" "${bazel_output}"
export INVALID_VERSION_ARGS="|-v|-version|"
"${runner}" --strict shellcheck check.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:shellcheck" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]

# A mismatched local version uses the Bazel target.
rm -f "${tool_output}" "${version_args_output}" "${bazel_output}"
export FAKE_VERSION="0.9.0"
"${runner}" shellcheck check.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:shellcheck" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]

# An unavailable local tool uses the Bazel target.
rm -f "${tool_output}" "${version_args_output}" "${bazel_output}"
"${runner}" missing-tool check.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:missing-tool" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]
