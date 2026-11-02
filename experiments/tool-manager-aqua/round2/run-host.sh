#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# Reproduce the test; this is not a product release dispatcher.
set -euo pipefail
probe_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export AQUA_ROOT_DIR=/tmp/score-aqua-eval/root
export UV_CACHE_DIR=/tmp/score-aqua-eval/uv-cache
export UV_PYTHON_INSTALL_DIR=/tmp/score-aqua-eval/python
export PRE_COMMIT_HOME=/tmp/score-aqua-round2/c2-precommit
export TEST_RUFF_COMMAND="$(python3 -c 'import json,sys; print(json.dumps(["/tmp/score-aqua-eval/bootstrap/aqua", "-c", sys.argv[1], "exec", "--", "ruff"]))' "${probe_dir}/aqua.yaml")"
export TEST_PRE_COMMIT_COMMAND="$(python3 -c 'import json,sys; print(json.dumps(["/tmp/score-aqua-eval/bin/uv", "run", "--no-project", "--no-config", "--isolated", "--with-requirements", sys.argv[1], "pre-commit"]))' "${probe_dir}/requirements.txt")"
exec python3 "${probe_dir}/round2/consumer_fixture.py"
