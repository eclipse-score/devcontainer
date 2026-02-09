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
# SPDX-FileCopyrightText: Copyright (c) 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -exuo pipefail

# This script runs opengrep in such a way that it only works on the changeset that is to be checked
# when running opengrep in the scope of a precommit hook.
# The CI system runs the same script, but in that context no changeset exists, so all files are to
# be checked. This also solves the problem that it is technically possible to work around the
# precommit checks.

changeset="$(git diff --staged --diff-filter=ACM --name-only)"
length="${#changeset}"
if [[ ${length} -gt 2048 ]]; then
  # The changeset is too long, it would result in errors from opengrep/underlying OS about filenames
  # being too long. Workaround: ignore the changeset and run opengrep on all files.
  changeset=""
fi
if [[ -z "${changeset}" ]]; then
  # Limit concurrency to 2 threads to reduce memory consumption
  OPENGREP_MAX_CONCURRENCY="--jobs=1"
  # No changeset, run opengrep on all files
  changeset="."
  opengrep scan "${OPENGREP_MAX_CONCURRENCY}" --error --disable-version-check --skip-unknown-extensions --emacs --sarif-output=build/opengrep.sarif -f ./opengrep/mandatory/ "${changeset}"
else
  # When changing ${changeset} to "${changeset}" it will break the script, ${changeset} actually contains *multiple* filenames
  # shellcheck disable=SC2086
  opengrep scan --error --disable-version-check --skip-unknown-extensions --emacs -f ./opengrep/mandatory/ ${changeset}
fi
