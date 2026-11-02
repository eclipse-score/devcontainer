#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail
probe_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
image="score-tool-manager-comparison-base:20261031"
expected="sha256:1b1ebf493ffb1a5a3a4d3c4c2a822cfe0da563d7028159078b0a02a12122a28d"
[[ "$(docker image inspect --format '{{.Id}}' "$image")" == "$expected" ]]
# Reuse round-one's fresh version-only preparation. Keep absolute venv/shebang
# paths stable; mount only Ruff and pre-commit, not mise, uv or their caches.
install_root=/tmp/score-mise-evaluation-fresh/data/installs
ruff_root="${install_root}/aqua-astral-sh-ruff/0.11.13"
python_root="${install_root}/pypi-pre-commit/4.7.0"
docker run --rm --network=none --user=12345:12345 \
  --tmpfs /work:rw,mode=1777 \
  --mount "type=bind,src=${ruff_root},dst=${ruff_root},readonly" \
  --mount "type=bind,src=${python_root},dst=${python_root},readonly" \
  --mount "type=bind,src=${probe_dir}/direct-smoke.sh,dst=/probe/direct-smoke.sh,readonly" \
  --env HOME=/work/home \
  --env "PATH=${ruff_root}/.mise-bins:${python_root}/bin:/usr/bin:/bin" \
  --workdir /work \
  "$image" bash -c 'set -eu; test "$(id -u)" = 12345; for manager in mise aqua nix uv; do ! command -v "$manager"; done; bash /probe/direct-smoke.sh' \
  | tee "${probe_dir}/round2-runtime.log"
