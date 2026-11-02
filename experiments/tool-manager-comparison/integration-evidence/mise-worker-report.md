<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M6 mise handoff

**Candidate:** `/home/alex/git/etas-contrib/score_devcontainer-eval-mise`
**Source base:** `2e337e41fba86ea7a94ee3d5e58cf3c4f7d93561` (unchanged; no commit)
**Status:** bounded M6 implementation and local checks are complete; stable for root integration gates. Root's clean generic Node lifecycle had one failure, this worker fixed the cause and verified the PyPI backend locally, and the root lifecycle retry remains pending.

## Implemented

- `tools/internal/mise/provision.py` maintains `.score-mise-ownership.json` beside each exposed bin directory. `flock` serializes shared-bin updates. Reprovisioning removes a deselected path only when the exact recorded symlink remains. A second environment's ownership keeps the shared command exposed. User replacements are preserved and reported; foreign or untracked selected-name collisions fail closed. Unrelated commands remain untouched.
- The experimental M5 auto-adoption/recovery path was removed after root review. Start with a fresh bin directory; existing selected commands without a M6 ownership record are unsupported and cause a clear failure.
- `tools/internal/mise/refresh.py` no longer reads or writes `experiments/`.
- `tools/internal/mise/python_package.py` builds and checks a local ordinary dependency wheel. `--version` and `--package-name` are required. PEP 621 extras derive pins from the direct mise owners and compatibility catalog. The local manifest binds package identity/version, root Python floor, extras, selected pins, owner hashes and wheel digest. The package has no SCORE runner entry point.
- `tools/BUILD.bazel` adds a focused Python package test and retains all existing Bazel contracts and labels. The experimental reference preparation helper now calls the maintained metadata generator.

## Checks passed

- `python3 -m unittest tools.tests.test_mise_provision tools.tests.test_mise_python_package` — 10 tests passed, including shared ownership, last-owner removal, user replacement and untracked-command rejection.
- Ruff check and format check on the changed Python files; Buildifier check on `tools/BUILD.bazel`.
- `python3 tools/internal/mise/refresh.py --check`; `python3 tools/internal/sync_readme.py --check`; `git diff --check`.
- `bazelisk test //tools:mise_provision_test //tools:mise_python_package_test //tools:python_tool_runner_test //tools:run_tool_test --test_output=errors` — all four targets passed; the two existing contract tests were cached.
- Built `/tmp/score-m6-mise/python-dependencies-final/dist/score_mise_dependencies-0.6.1-py3-none-any.whl` with explicit local identity `score-mise-dependencies`, then `python3 tools/internal/mise/python_package.py check /tmp/score-m6-mise/python-dependencies-final` passed. This is a local candidate identity only; no public package identity or hosting policy was selected.
- A normal uv consumer at `/tmp/score-m6-mise/consumer-final` passed `uv lock`, `uv sync`, `uv run ruff --version` (`0.11.13`) and `uv run pre-commit --version` (`4.7.0`). A direct `uvx --from 'score-mise-dependencies[ruff] @ file:///tmp/score-m6-mise/python-dependencies-final/dist/score_mise_dependencies-0.6.1-py3-none-any.whl' ruff --version` also returned `ruff 0.11.13`. It used no SCORE wrapper. The generated Python floor is `>=3.11`, taken from the root project metadata.
- Reused `/tmp/score-m5-mise/provision-data` and `/tmp/score-m3-mise/bootstrap/mise` without copying their payloads. Provisioned repository and bazel-feature into fresh `/tmp/score-m6-mise/provision-bin`; a bounded shared-selection exercise preserved Bazelisk/Buildifier for bazel-feature while retiring repository-only Ruff. Strict host commands with `PATH=/usr/bin:/bin` returned uvx `0.13.6` and Starpls `0.1.22` with Bazel absent from PATH.
- Diagnosed the clean lifecycle failure in `/tmp/score-m6-gates/mise-lifecycle-20261102T002835Z-dc12f30c/lifecycle.log`: the provisioner put mise's uv `install_path` on PATH, while its executable is nested one directory lower. Updated `provision.py` to resolve the actual selected uv executable, expose its parent directory, set `MISE_PYPI_UVX=true`, and stop before PyPI installation if the selected uv pin is missing or inactive. This prevents another pipx fallback when the required uv is unavailable.
- Added regression coverage for the nested install layout with an empty ambient PATH and for failing before PyPI install when pinned uv is unresolved. `python3 -m unittest tools.tests.test_mise_provision tools.tests.test_mise_python_package` passes 11 tests; Ruff check/format and `git diff --check` pass. All four focused Bazel targets pass; `mise_provision_test` ran and the other three were cached.
- Actual fresh-data smoke reused only the cached pinned uv executable, installed `pypi:pre-commit@4.7.0` with mise's `uv tool install`, and `mise exec -- pre-commit --version` returned `pre-commit 4.7.0`. It used no pipx. The root generic Node lifecycle retry and image gates remain root-owned; this worker did not launch them.

## Source maintenance ledger

| Responsibility | Maintained owner |
| --- | --- |
| Shared selection policy | `tools/environments.json` carries environment membership; direct version owners remain in `tools/mise/*.toml`. |
| Manager-native behavior | mise installs and resolves selected backends into its install tree and maintains native artifact locks. |
| SCORE adapter | `provision.py` maps selections to backend/entrypoint, creates direct command links and reconciles their per-environment ownership. `refresh.py` exports portable Bazel compatibility metadata. |
| Ordinary Python package | `python_package.py` renders standard extras, builds the local wheel and checks release metadata from the direct owners. |
| One-time work | M1–M5 installer callers/removal remain inherited. M6 adds the ownership ledger and shared-selection reconciliation; first setup requires a fresh bin prefix. The package generator and check now have maintained `tools/` paths. |
| Recurring work | Renovate updates direct owners and `refresh.sh` refreshes locks/compatibility outputs. Provisioning reconciles membership changes. Each package build takes an explicit version and identity, then uses the maintained check. |

## Root-scheduled gates (retry not run here)

The image build and clean root generic Node lifecycle retry remain with the integration owner. The first clean lifecycle failed at `pypi:pre-commit` as described above; this worker fixed the adapter and verified the PyPI backend in a fresh local data directory. From the repository root:

```console
./scripts/build.sh --amd64 score-m6-mise
docker run --rm --entrypoint /bin/bash ghcr.io/eclipse-score/devcontainer:score-m6-mise-amd64 -lc 'uv --version && uvx --version && pre-commit --version && starpls version'
devcontainer up --workspace-folder "$PWD" --config .devcontainer/devcontainer.json
devcontainer exec --workspace-folder "$PWD" --config .devcontainer/devcontainer.json bash -lc 'uv --version && uvx --version && pre-commit --version && uvx --from "codespell==2.4.1" codespell --version'
```

No ARM Linux or macOS execution, image build, lifecycle retry, publication, commit or push was performed by this worker. The root-owned clean generic Node lifecycle was run once and failed before the fix.
