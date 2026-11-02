#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail
probe_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
state="${PROBE_STATE_DIR:-$(mktemp -d /tmp/score-aqua-smoke.XXXXXX)}"
export AQUA_ROOT_DIR="${state}/aqua"
export UV_CACHE_DIR="${state}/uv-cache"
export UV_PYTHON_INSTALL_DIR="${state}/python"
export PRE_COMMIT_HOME="${state}/pre-commit"
aqua_bin="${AQUA_BINARY:-aqua}"

# Build-time export uses aqua's own recipes/checksums. Executing the copied
# native binaries later needs no aqua shim or runtime install.
"${aqua_bin}" -c "${probe_dir}/aqua.yaml" cp --tags container -o "${state}/bin"
"${state}/bin/ruff" --version
"${state}/bin/uv" run --no-project --no-config --isolated \
    --with-requirements "${probe_dir}/requirements.txt" pre-commit --version

printf 'import os\n' > "${state}/fixture.py"
status=0
"${state}/bin/ruff" check --isolated "${state}/fixture.py" || status=$?
[[ "${status}" == 1 ]]

mkdir -p "${state}/consumer"
git -C "${state}/consumer" init --quiet
cat > "${state}/consumer/.pre-commit-config.yaml" <<'CONFIG'
repos:
  - repo: local
    hooks:
      - id: local-success
        name: local success
        language: system
        entry: python3 -c 'import sys; sys.exit(0)'
        always_run: true
        pass_filenames: false
CONFIG
cd "${state}/consumer"
"${state}/bin/uv" run --no-project --no-config --isolated \
    --with-requirements "${probe_dir}/requirements.txt" pre-commit run --all-files
