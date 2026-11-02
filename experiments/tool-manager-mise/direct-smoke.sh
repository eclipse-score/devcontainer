#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# Executes prepared tools only; deliberately no manager or installer command.
set -euo pipefail
mkdir -p "${HOME}" consumer
cd consumer
git init -q
export EXPECTED_CWD="$PWD"
printf 'import os\n' > 'fixture with space.py'
ruff --version
pre-commit --version
status=0
ruff check --isolated 'fixture with space.py' || status=$?
[[ "$status" == 1 ]]
printf 'Ruff diagnostic exit: %s\n' "$status"
printf 'print("ready")\n' > 'fixture with space.py'
git add 'fixture with space.py'
cat > .pre-commit-config.yaml <<'YAML'
repos:
  - repo: local
    hooks:
      - id: observe-cwd
        name: Observe consumer cwd
        language: system
        entry: >-
          python3 -c 'import os,sys; print(os.getcwd()); assert os.getcwd()==os.environ["EXPECTED_CWD"]; assert sys.argv[1:]==["marker value"]' 'marker value'
        pass_filenames: false
YAML
pre-commit run observe-cwd --all-files --verbose
