#!/usr/bin/env bash
set -euo pipefail
prefix=/tmp/score-own-copilot/published-prepared
export UV_CACHE_DIR="${prefix}/cache"
export UV_PYTHON=/usr/bin/python3
python3 - <<'PY'
import hashlib
import json
from pathlib import Path
root = Path("/usr/local/share/score-tools")
paths = [
    root / "score_tools/provision.py", root / "score_tools/catalog.py",
    root / "internal/provision.py", root / "internal/devcontainer/install.py",
    root / "score_tools/python_tools.bzl", root / "environments.json",
    *sorted((root / "lockfiles").glob("*.lock.json")),
    Path("/own-test-project/test.sh"),
    Path("/devcontainer/features/s-core-local/tests/test_default.sh"),
    Path("/devcontainer/features/bazel/tests/test_default.sh"),
]
Path("/tmp/score-own-copilot/published-prepared/source-hashes.json").write_text(json.dumps({
    str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths
}, indent=2) + "\n")
PY
python3 /usr/local/share/score-tools/internal/provision.py published \
    --catalog-root /own-runtime-catalog \
    --prefix "${prefix}" \
    --native actionlint apm bazelisk buildifier opencode ruff shellcheck starpls uv uvx yamlfmt \
    --python basedpyright pre-commit pytest > "${prefix}/provision.json"
export PATH="${prefix}/bin:${PATH}"
su vscode -c "PATH='${prefix}/bin':\"\$PATH\" HOME=/home/vscode bash -lc 'export PATH=\"${prefix}/bin:\$PATH\"; bash /own-test-project/test.sh'" \
    > "${prefix}/feature-tests.log" 2>&1
