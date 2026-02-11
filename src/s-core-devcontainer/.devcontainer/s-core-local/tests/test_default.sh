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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -euo pipefail

ARCHITECTURE=$(dpkg --print-architecture)
KERNEL=$(uname -s)

# Read tool versions + metadata into environment variables
. /devcontainer/features/s-core-build/versions.sh /devcontainer/features/s-core-local/versions.yaml

# Common tooling
check "validate shellcheck is working and has the correct version" bash -c "shellcheck --version | grep '${shellcheck_version}'"

# Common tooling
check "validate git is working and has the correct version" bash -c "git --version | grep '${git_version}'"
check "validate git-lfs is working and has the correct version" bash -c "git lfs version | grep '${git_lfs_version}'"

# additional developer tools
check "validate gdb is working and has the correct version" bash -c "gdb --version | grep '${gdb_version}'"
check "validate gh is working and has the correct version" bash -c "gh --version | grep '${gh_version}'"
check "validate valgrind is working and has the correct version" bash -c "valgrind --version | grep '${valgrind_version}'"
if [ "${ARCHITECTURE}" = "amd64" ] || { [ "${ARCHITECTURE}" = "arm64" ] && [ "${KERNEL}" = "Darwin" ]; }; then
    check "validate codeql is working and has the correct version" bash -c "codeql --version | grep '${codeql_version}'"
fi
