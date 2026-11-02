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

owner_dir=${1:?aqua owner directory is required}
prefix=${2:-/opt/score-tools}
platform=${SCORE_AQUA_PLATFORM:-}
bootstrap_dir=$(mktemp -d /tmp/score-aqua-bootstrap.XXXXXX)
trap 'rm -rf "${bootstrap_dir}"' EXIT

bootstrap_args=(
    --output-dir "${bootstrap_dir}"
    --owner-dir "${owner_dir}"
)
if [[ -n "${platform}" ]]; then
    bootstrap_args+=(--platform "${platform}")
fi
python3 /usr/local/share/score-tools/internal/devcontainer/bootstrap_aqua.py "${bootstrap_args[@]}"

export AQUA_BINARY="${bootstrap_dir}/aqua"
export AQUA_ROOT_DIR="${bootstrap_dir}/root"
python3 /usr/local/share/score-tools/internal/devcontainer/provision_host_tools.py \
    --profile published \
    --prefix "${prefix}" \
    --owner-dir "${owner_dir}"
chmod -R a+rX "${prefix}"
