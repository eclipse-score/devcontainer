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
# Initial online installation: aqua + uv are build-time prerequisites only.
# Provision at its final absolute prefix against the target OS/Python ABI.
set -euo pipefail
profile=${1:?profile required}
prefix=${2:-/opt/score-tools}
release=$(cd "$(dirname "$0")" && pwd)
aqua=${AQUA_BINARY:-aqua}
uv=${UV_BINARY:-uv}
export AQUA_POLICY_CONFIG="${release}/aqua-policy.yaml${AQUA_POLICY_CONFIG:+:${AQUA_POLICY_CONFIG}}"
mkdir -p "${prefix}/bin"
# APM's frozen Python runtime is stored next to its executable, so retain that
# package tree instead of exposing aqua's proxy or only the copied binary.
if [[ ${NATIVE_PREPARED:-0} != 1 ]]; then
    "${aqua}" -c "${release}/aqua.yaml" cp --tags "${profile}" -o "${prefix}/bin"
    if [[ "${profile}" == published ]]; then
        "${aqua}" -c "${release}/aqua.yaml" install --tags "${profile}"
        apm_binary=$("${aqua}" -c "${release}/aqua.yaml" which apm)
        apm_runtime=$(dirname -- "${apm_binary}")
        mkdir -p "${prefix}/lib/apm"
        cp -a "${apm_runtime}/." "${prefix}/lib/apm/"
        rm -f "${prefix}/bin/apm"
        ln -s ../lib/apm/apm "${prefix}/bin/apm"
    fi
fi
"${uv}" --no-config venv --python /usr/bin/python3 "${prefix}/python"
"${uv}" --no-config pip install --python "${prefix}/python/bin/python" -r "${release}/${profile}.requirements.txt"
# Expose installed CLIs without exposing the build-time manager on runtime PATH.
"${prefix}/python/bin/python" - "${prefix}" "${release}/${profile}.requirements.txt" <<'PYTHON'
from importlib.metadata import distribution
from pathlib import Path
import sys
prefix = Path(sys.argv[1])
for requirement in Path(sys.argv[2]).read_text().splitlines():
    for entry in distribution(requirement.split("==")[0]).entry_points:
        if entry.group == "console_scripts":
            (prefix / "bin" / entry.name).symlink_to("../python/bin/" + entry.name)
PYTHON
chmod -R a+rX "${prefix}"
