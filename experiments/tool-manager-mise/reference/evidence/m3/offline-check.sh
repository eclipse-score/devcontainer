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

workspace=/workspace
tmp="$(mktemp -d /tmp/score-mise-m3-offline.XXXXXX)"
installer=/usr/local/share/score-tools/internal/devcontainer/install.py
export RUFF_CACHE_DIR="${tmp}/ruff-cache"
export UV_CACHE_DIR="${tmp}/uv-cache"

# Existing feature verifiers execute the actual selections and inspect APT
# state. Bazelisk receives the same explicit preinstall choice as its feature.
"${installer}" verify-environment s-core-local
"${installer}" verify-environment bazel-feature
USE_BAZEL_VERSION=8.6.0 bazel version
python3 - <<'PY'
import hashlib
import json
import os
from pathlib import Path

manifest = json.loads(
    Path("/usr/local/share/score-tools/prepared-tools.json").read_text()
)
for name, record in manifest["tools"].items():
    link = Path("/usr/local/bin") / name
    executable = Path(record["executable"])
    assert link.is_symlink(), f"feature replaced prepared PATH link: {name}"
    assert os.path.samefile(link, executable), f"PATH differs from handoff: {name}"
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    assert digest == record["sha256"], f"prepared executable changed: {name}"
print(f"Verified {len(manifest['tools'])} prepared PATH links and runtime digests.")
PY

cat > "${tmp}/test_prepared_tool.py" <<'PY'
def message(name: str) -> str:
    return f"hello {name}"


def test_message() -> None:
    assert message("S-CORE") == "hello S-CORE"
PY

ruff check "${tmp}/test_prepared_tool.py"
ruff format --check "${tmp}/test_prepared_tool.py"
pytest -q "${tmp}/test_prepared_tool.py"
basedpyright "${tmp}/test_prepared_tool.py"

cat > "${tmp}/bad.py" <<'PY'
value: str = 42
PY
if basedpyright "${tmp}/bad.py" > "${tmp}/basedpyright.log" 2>&1; then
    echo "basedpyright accepted an incompatible assignment" >&2
    exit 1
fi
grep -q "reportAssignmentType" "${tmp}/basedpyright.log"

# A local system hook exercises pre-commit's normal file filtering and failure
# reporting without cloning hook repositories while the container has no net.
precommit_repo="${tmp}/pre-commit-repo"
mkdir -p "${precommit_repo}"
git -C "${precommit_repo}" init -q
cat > "${precommit_repo}/.pre-commit-config.yaml" <<'YAML'
repos:
  - repo: local
    hooks:
      - id: selected-ruff
        name: selected Ruff
        entry: ruff check --select F401
        language: system
        types: [python]
YAML
cp "${tmp}/test_prepared_tool.py" "${precommit_repo}/test_prepared_tool.py"
git -C "${precommit_repo}" add .pre-commit-config.yaml test_prepared_tool.py
(cd "${precommit_repo}" && PRE_COMMIT_HOME="${tmp}/pre-commit-home" \
    pre-commit run --all-files)
cat > "${precommit_repo}/unused.py" <<'PY'
import os
PY
git -C "${precommit_repo}" add unused.py
if (cd "${precommit_repo}" && PRE_COMMIT_HOME="${tmp}/pre-commit-home" \
    pre-commit run --files unused.py); then
    echo "pre-commit accepted a Ruff failure" >&2
    exit 1
fi

# In container mode both ordinary and strict execution resolve the installed
# PATH command directly; the existing runner test below covers strict host mode
# and confirms it retains its pinned Bazel target.
export RUN_TOOL_CONTAINER_MODE=container
"${workspace}/tools/run-tool" shellcheck --version
"${workspace}/tools/run-tool" --strict shellcheck --version
TEST_TMPDIR="${tmp}/run-tool-test" \
TEST_SRCDIR="${workspace}" \
TEST_WORKSPACE=. \
    bash "${workspace}/tools/tests/run_tool_test.sh"

echo "Offline prepared-runtime checks passed as $(id -un) (uid=$(id -u))."
