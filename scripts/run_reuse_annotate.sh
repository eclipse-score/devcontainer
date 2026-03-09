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

set -euxo pipefail

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")

pushd "${SCRIPT_DIR}/.." > /dev/null

files_to_annotate=$(git ls-files)

# remove deleted files from the list of files to annotate
deleted_files=$(git ls-files --deleted)
files_to_annotate=$(comm -23 <(git ls-files | sort) <(echo "${deleted_files}" | sort))

# shellcheck disable=SC2086
# Expansion of ${files_to_annotate} is intentional to pass the list of files as separate arguments to the reuse annotate command.
pipx run reuse annotate --template apache-2.0 --merge-copyrights --recursive --skip-unrecognised \
 --copyright="Contributors to the Eclipse Foundation" --license=Apache-2.0 ${files_to_annotate}

popd > /dev/null
