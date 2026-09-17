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
installer="${runfiles_root}/tools/internal/devcontainer/install.py"
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

cat > "${fake_bin}/special-tool" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
tool_name=$(basename "$0")
case "${tool_name}" in
    bazelisk) version="1.27.0" ;;
    starpls) version="0.1.22" ;;
    *) exit 1 ;;
esac
if [[ "$#" -eq 1 && "$1" == version ]]; then
    printf '%s\n' "$1" >> "${VERSION_ARGS_OUTPUT}"
    printf '%s %s\n' "${tool_name}" "${version}"
    exit 0
fi
if [[ "$#" -gt 0 ]]; then
    printf '%s\n' "$@" > "${TOOL_OUTPUT}"
fi
EOF
chmod +x "${fake_bin}/shellcheck" "${fake_bin}/bazel" \
    "${fake_bin}/unknown-tool" "${fake_bin}/special-tool"
ln -s special-tool "${fake_bin}/bazelisk"
ln -s special-tool "${fake_bin}/starpls"

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
export RUN_TOOL_CONTAINER_MODE=host
export INVALID_VERSION_ARGS="|-v|-version|"
export SUCCESS_VERSION_ARG="--version"

reset_outputs() {
    rm -f "${tool_output}" "${version_args_output}" "${bazel_output}"
}

# A tool may reject -v and -version; the runner must continue to --version.
export FAKE_VERSION="0.10.0"
reset_outputs
"${runner}" shellcheck --help
assert_lines "${version_args_output}" -v -version --version
assert_lines "${tool_output}" --help
[[ ! -e "${bazel_output}" ]]

# Bazelisk and Starpls must use only their explicit version subcommand; their
# --version output describes the Bazel or language-server release instead.
reset_outputs
"${runner}" bazelisk check.sh
assert_lines "${version_args_output}" version
assert_lines "${tool_output}" check.sh
[[ ! -e "${bazel_output}" ]]

reset_outputs
"${runner}" starpls check.sh
assert_lines "${version_args_output}" version
assert_lines "${tool_output}" check.sh
[[ ! -e "${bazel_output}" ]]

# When no version flag returns a parseable version, installed_version returns 1
# and the runner must fall back to Bazel.
reset_outputs
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
reset_outputs
"${runner}" unknown-tool check.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:unknown-tool" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]

# Without Bazel, an unavailable tool must report exit status 127.
no_bazel_bin="${TEST_TMPDIR}/no-bazel-bin"
mkdir -p "${no_bazel_bin}"
if PATH="${no_bazel_bin}" /bin/bash "${runner}" missing-tool check.sh \
    > "${TEST_TMPDIR}/no-bazel.output" 2>&1; then
    echo "runner unexpectedly succeeded without Bazel" >&2
    exit 1
else
    no_bazel_status=$?
fi
[[ "${no_bazel_status}" -eq 127 ]]
grep -Fx "Could not run 'missing-tool': no container command or Bazel executable is available." \
    "${TEST_TMPDIR}/no-bazel.output"

# Strict mode always uses the Bazel target.
reset_outputs
export INVALID_VERSION_ARGS="|-v|-version|"
"${runner}" --strict shellcheck check.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:shellcheck" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]

# A mismatched local version uses the Bazel target.
reset_outputs
export FAKE_VERSION="0.9.0"
"${runner}" shellcheck check.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:shellcheck" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]

# An unavailable local tool uses the Bazel target.
reset_outputs
"${runner}" missing-tool check.sh
assert_lines "${bazel_output}" \
    "run" \
    "@score_devcontainer//tools:missing-tool" \
    "--" \
    "check.sh"
[[ ! -e "${tool_output}" ]]

# The runner embeds the catalog as a shell function; extract and evaluate only
# that generated function so the test can compare it with the source catalog.
# shellcheck disable=SC1090
eval "$(sed -n '/^pinned_version() {/,/^}/p' "${runner}")"

catalog_versions="${TEST_TMPDIR}/catalog-versions"
runner_versions="${TEST_TMPDIR}/runner-versions"

python3 -c '
import sys
from pathlib import Path
sys.path.insert(0, str(Path("'"${installer}"'").parent))
from install import load_catalog_versions
for tool, ver in sorted(load_catalog_versions().items()):
    print(f"{tool}={ver}")
' > "${catalog_versions}"

while IFS='=' read -r tool expected_ver; do
    actual_ver="$(pinned_version "${tool}")"
    [[ "${actual_ver}" == "${expected_ver}" ]] || {
        printf 'pinned_version mismatch for %s: expected %s, got %s\n' \
            "${tool}" "${expected_ver}" "${actual_ver}" >&2
        exit 1
    }
    printf '%s=%s\n' "${tool}" "${actual_ver}" >> "${runner_versions}"
done < "${catalog_versions}"

diff -u "${catalog_versions}" "${runner_versions}"

# An uncatalogued tool must return non-zero from pinned_version.
if pinned_version "unknown-tool" >/dev/null 2>&1; then
    echo "pinned_version unexpectedly succeeded for unknown-tool" >&2
    exit 1
fi
