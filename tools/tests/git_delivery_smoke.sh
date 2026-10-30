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

# Exercise the installed distribution outside the checkout. This only reads a
# local Git commit; it never creates a tag, pushes, or publishes a package.
set -euo pipefail

repository_root="$(git rev-parse --show-toplevel)"
reference="${1:-$(git rev-parse HEAD)}"
uv_command="$(command -v uv)"
package="git+file://${repository_root}@${reference}"
smoke_directory="$(mktemp -d)"
trap 'rm -rf "${smoke_directory}"' EXIT

cd "${smoke_directory}"
"${uv_command}" tool run --from "${package}" score-tool pre-commit --version

# The package must carry its literal definitions; no checkout or container
# installer is available in this execution environment.
"${uv_command}" run --no-project --with "${package}" python -c '
from importlib.resources import files
from score_tools.catalog import _load_python_tools
assert files("score_tools").joinpath("python_tools.bzl").is_file()
assert _load_python_tools()["pre-commit"]["entrypoint"] == "pre-commit"
'

mkdir fake-bin
cat > fake-bin/uv <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "${PWD}" "$@" > "${SCORE_SMOKE_OUTPUT}"
exit 42
EOF
chmod +x fake-bin/uv

# Launch with the real uv, then let the installed package find a controlled uv
# on PATH. This tests the installed console script's process boundary, including
# cwd, empty arguments, quoting, and the exact returned tool status.
set +e
PATH="${smoke_directory}/fake-bin:${PATH}" SCORE_SMOKE_OUTPUT="${smoke_directory}/actual" \
    "${uv_command}" tool run --from "${package}" score-tool pre-commit run "argument with spaces" ""
status=$?
set -e
[[ "${status}" -eq 42 ]]

# Read the expected immutable requirement from the installed package, too.
requirement="$("${uv_command}" run --no-project --with "${package}" python -c '
from score_tools.catalog import _load_python_tools
x = _load_python_tools()["pre-commit"]
print(x["package"] + "==" + x["version"])
')"
printf '%s\n' "${smoke_directory}" tool run --from "${requirement}" pre-commit run "argument with spaces" "" > expected
diff -u expected actual
