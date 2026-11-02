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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# Shared external behavior check, invoked inside each prepared reference runtime.
set -euo pipefail
: "${SCORE_REFERENCE_PROFILE:?published or repository required}"
: "${SCORE_EXPECT_RUFF:?expected Ruff version required}"
: "${SCORE_EXPECT_PRE_COMMIT:?expected pre-commit version required}"
test "$(id -u)" = 12345
for manager in mise aqua nix uv uvx; do
    if command -v "${manager}" >/dev/null 2>&1; then
        echo "Unexpected runtime manager on PATH: ${manager}" >&2
        exit 1
    fi
done
ruff --version | tee /tmp/score-reference-ruff-version.txt
test "$(cat /tmp/score-reference-ruff-version.txt)" = "ruff ${SCORE_EXPECT_RUFF}"
pre-commit --version | tee /tmp/score-reference-precommit-version.txt
test "$(cat /tmp/score-reference-precommit-version.txt)" = "pre-commit ${SCORE_EXPECT_PRE_COMMIT}"
case "${SCORE_REFERENCE_PROFILE}" in
    published)
        : "${SCORE_EXPECT_SHELLCHECK:?expected ShellCheck version required}"
        shellcheck --version
        test "$(shellcheck --version | awk '/^version:/ { print $2 }')" = "${SCORE_EXPECT_SHELLCHECK}"
        ;;
    repository)
        if command -v shellcheck >/dev/null 2>&1; then
            echo 'ShellCheck leaked into repository selection' >&2
            exit 1
        fi
        ;;
    *) echo 'Unknown reference profile' >&2; exit 2 ;;
esac
consumer=$(mktemp -d /tmp/score-reference-consumer.XXXXXX)
cd "${consumer}"
git init -q
printf 'import os\n' > 'fixture with space.py'
# The unquoted positional parameter is the intentional ShellCheck fixture.
# shellcheck disable=SC2016
printf '#!/bin/sh\necho $1\n' > 'fixture with space.sh'
printf 'selected consumer\n' > .score-probe-marker
cat > .pre-commit-config.yaml <<'HOOKS'
repos:
  - repo: local
    hooks:
      - id: observe-cwd
        name: Observe consumer cwd and arguments
        language: system
        entry: sh -c 'test "$1" = "marker value" && test -f .score-probe-marker && pwd' sh
        args: ['marker value']
        pass_filenames: false
        always_run: true
HOOKS
git add .
status=0
ruff check --isolated 'fixture with space.py' > ruff.log 2>&1 || status=$?
cat ruff.log
test "${status}" = 1
# grep is part of the common Ubuntu base; the candidate need not provide rg.
grep -q F401 ruff.log
if [[ "${SCORE_REFERENCE_PROFILE}" = published ]]; then
    status=0
    shellcheck 'fixture with space.sh' > shellcheck.log 2>&1 || status=$?
    cat shellcheck.log
    test "${status}" = 1
    grep -q SC2086 shellcheck.log
fi
pre-commit run --all-files --verbose
printf 'Reference runtime passed: profile=%s uid=%s cwd=%s\n' \
    "${SCORE_REFERENCE_PROFILE}" "$(id -u)" "${PWD}"
