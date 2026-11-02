<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M7 mise handoff

**State:** stable for root comparison. All M7 work used only the mise
candidate and `/tmp/score-m7-mise`; inherited M1–M6 dirty changes remain
preserved. No pin or maintained production source changed in M7. The only
candidate addition is
[`README-m7.md`](/home/alex/git/etas-contrib/score_devcontainer-eval-mise/experiments/tool-manager-mise/reference/README-m7.md).
No commits, pushes, publication, full image build, or winner/adoption claim.

## Outcome

- Provisioned the published `s-core-local` + `bazel-feature` selected profile
  from the maintained mise bootstrap and `provision.py` into a fresh ARM64
  data/bin prefix. All selected versions stayed unchanged; 15 commands are
  fingerprinted in `result.json`.
- Runtime checks used `score-tooling-reference:final-arm64`, Ubuntu 24.04.5,
  Python 3.12.3, ARM64 under QEMU user emulation on an amd64 Docker host. The
  final runtime and wheel consumer were uid 1000, networkless, and had
  read-only root filesystems. This does not claim physical ARM execution.
- Direct and strict prepared Ruff/pre-commit results matched; poison manager
  and Bazel executables remained untouched. The offline functional checks
  passed, including `uvx` using the local dependency wheel, the expected Ruff
  `F821` and codespell typo failures, pytest, pre-commit config validation,
  basedpyright, Actionlint, ShellCheck, and Buildifier.
- Bazelisk 1.27.0 was executed only through the no-fallback guard. It exited 1
  with the expected “not allowed to use fallback version” result; no Bazel was
  downloaded or run. A standalone Bazelisk self-version string was not
  available at the selected pin in the offline test.
- Built and checked a local normal dependency wheel
  (`score-mise-dependencies` 0.6.1; SHA-256
  `2518871b2c815a56480f1f35c370eca02af52e67e0bed606efeec4fcb98b73a1`). The
  offline consumer completed `uv lock`, `uv sync`, and `uv run`; separate
  offline `uvx --from <local wheel>[ruff]` returned Ruff 0.11.13. No public
  package identity or host was selected and nothing was published.
- Static macOS ARM review found URL/checksum data for all ten native/published
  lock records and the bootstrap, and generic Python/uv resolution for the
  four PyPI tools. No macOS execution occurred.
- The maintained `refresh.py --check`, local package release check and
  `git diff --check` passed. Root’s latest M6 comparison records all six root
  gates passed.

## Reproduction and evidence

The exact bootstrap, provisioning, wheel build/check, cache preparation,
offline runtime, consumer, version and behavior commands are in candidate
`README-m7.md` and structured `result.json`. Fresh prefix:
`/tmp/score-m7-mise/runtime`; logs and probes are under
`/tmp/score-m7-mise/{logs,probes}`. No full feature image was built.

Useful completed commands and captured results:

```console
docker exec score-m7-mise-arm64-runtime /tmp/score-m7-mise/probes/selected-versions.sh
# exit 0; selected prepared commands resolve inside the fresh M7 data prefix

docker exec score-m7-mise-arm64-runtime /tmp/score-m7-mise/probes/execute-behaviors.sh
# exit 0; direct/strict, offline Python and functional positive/negative probes pass

docker exec score-m7-mise-arm64-consumer /bin/bash -lc 'set -eu; id; uname -m; uv lock --offline; uv sync --offline; uv run --offline --no-sync ruff --version'
# exit 0; uid 1000, aarch64, local wheel installed, ruff 0.11.13

python3 tools/internal/mise/refresh.py --check
# Owner locks and compatibility outputs are current

python3 tools/internal/mise/python_package.py check /tmp/score-m7-mise/dependency-release
# Local dependency release matches current owners

git diff --check
# exit 0
```

Raw logs include corrected harness setup attempts: an initially unmounted uv
cache, a consumer cache without registry metadata, and an invalid temporary
pre-commit fixture. Each was corrected; final network-isolated probes above
passed. Early Bazelisk self-version attempts were stopped while resolving
Bazel; final guarded execution did not resolve/download it. These attempts are
recorded in the raw logs and do not indicate selected-tool install failure.

## Maintenance ledger

| Work | Owner / cadence |
| --- | --- |
| Selection and pins | `tools/environments.json`, `tools/mise/*.toml`, and generated artifact locks; update each version only at its owner. |
| Installation and command membership | Maintained `bootstrap.sh` and `provision.py` on setup/reprovision; prepare from a fresh target-platform prefix and reconcile the selected direct links. |
| Strict execution | Existing `tools/run-tool` direct host path and Bazel fallback; M7 verified direct mode without calling either fallback executable. |
| Python compatibility and release | `refresh.py` exports current owner data; `python_package.py` generates/checks a normal dependency wheel. Each release operator must choose an explicit version and package identity and later select hosting. |
| M7-only platform evidence | Fresh ARM64 provisioning and offline checks were performed once here. Future supported platforms need their own fresh-prefix execution; macOS ARM remains unexecuted. |

Root owns cross-candidate gates, shared comparison edits, and archival. Refer
to `/tmp/score-m7-mise/result.json` for container IDs, all command target and
source hashes, raw log hashes, exact results, and platform/user/network
limitations.
