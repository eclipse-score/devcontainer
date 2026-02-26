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

pipx run reuse lint

# Check that all files have Eclipse foundation copyright
# The copyright string is split in this way to avoid this file triggering a
# false positive, with the check below. Otherwise the string with backslashes
# around the C would be detected as violation.
c="Copyright"
holders="Contributors to the Eclipse Foundation"
files_without_eclipse_copyright="$(pipx run reuse lint --json | jq -r --arg c "${c}" --arg holders "${holders}" '.files[] | select(any(.copyrights[]; .value | test($c + " \\(C\\) 2026 " + $holders) | not)) | .path')"

if [[ -n "${files_without_eclipse_copyright}" ]]; then
  echo -e "\nThe following files do not have the correct copyright holder:"
  echo "${files_without_eclipse_copyright}"
  exit 1
else
  echo "All files have the correct copyright header."
fi
