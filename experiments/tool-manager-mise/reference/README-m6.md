<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Mise M6: command reconciliation and ordinary Python releases

**Status, 2026-11-02:** maintained mise provisioning now reconciles selected
commands per shared bin directory, and the ordinary dependency wheel generator
and release check live under `tools/`. Focused Python, Bazel, refresh, lint and
local uv/uvx checks passed. The root generic Node lifecycle exposed a PyPI
installer PATH issue; the maintained provisioner fix and a fresh-data mise
smoke passed, and the root lifecycle retry remains pending. No image build,
ARM execution, publication, commit or push was attempted. The comparison owner
serially schedules the image and lifecycle retry.

## Command ownership

`tools/internal/mise/provision.py` records environment-to-command-to-target
ownership in `.score-mise-ownership.json` beside the exposed links. A file lock
serializes updates when feature installers share `/usr/local/bin`.

Reprovisioning one environment removes only its old link when the link is still
the exact symlink recorded for that environment. A command with another
environment owner remains exposed. If an owner changes its pin, the provisioner
replaces the recorded symlink after resolving the selected executable. A user
replacement is left in place and reported; a selected command path with no
matching ownership record fails closed. Unrelated user commands are untouched.
Use a fresh bin directory on first setup: the unadopted M5 prefix layout is not
a supported ownership format.

The shared-selection check used the existing M5 mise data tree without copying
it and a fresh M6 bin directory. It provisioned `repository`, then
`bazel-feature`, and reconciled the repository selection with `bazelisk`,
`buildifier` and `ruff` removed. The shared Bazelisk and Buildifier links stayed
owned by `bazel-feature`; the repository-only Ruff link was retired. Strict
host calls then executed `uvx` and Starpls directly with Bazel absent from PATH.

The final cached-install provision and direct-execution commands were:

```console
python3 tools/internal/mise/provision.py repository --data-dir /tmp/score-m5-mise/provision-data --bin-dir /tmp/score-m6-mise/provision-bin --mise /tmp/score-m3-mise/bootstrap/mise
python3 tools/internal/mise/provision.py bazel-feature --data-dir /tmp/score-m5-mise/provision-data --bin-dir /tmp/score-m6-mise/provision-bin --mise /tmp/score-m3-mise/bootstrap/mise
PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host SCORE_TOOLS_BIN_DIR=/tmp/score-m6-mise/provision-bin tools/run-tool --strict uvx --version
PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host SCORE_TOOLS_BIN_DIR=/tmp/score-m6-mise/provision-bin tools/run-tool --strict starpls version
PATH=/tmp/score-m6-mise/provision-bin:/usr/bin:/bin uv --version
```

They returned uvx/uv 0.13.6 and Starpls 0.1.22. The shared-selection
deselection smoke used the same cached data and fresh bin directory; after
removing `bazelisk`, `buildifier` and `ruff` from the repository ownership map,
it confirmed that bazel-feature retained the first two and Ruff disappeared.
Focused tests also cover user replacement, untracked selected-name rejection,
foreign commands, same-name target conflicts and final-owner removal.

## Pinned uv for mise PyPI tools

The root generic Node post-create run installed native mise tools, then failed
while installing `pypi:pre-commit@4.7.0` because mise could not discover uv and
tried its pipx fallback. The log is
`/tmp/score-m6-gates/mise-lifecycle-20261102T002835Z-dc12f30c/lifecycle.log`.
The `uv` backend's reported `install_path` is a parent directory; its executable
is nested at `uv-x86_64-unknown-linux-gnu/uv`. The provisioner now resolves the
actual pinned executable, prepends its containing directory to mise's child
PATH, and explicitly sets `MISE_PYPI_UVX=true` before installing PyPI tools.

With an empty ambient PATH, the focused provisioner test verifies that the
PyPI install environment finds only the nested mise-managed uv. A real mise
smoke used a fresh data directory and the existing cached uv, then installed
and ran pre-commit without pipx:

```console
export MISE_DATA_DIR=/tmp/score-m6-mise/fresh-uv-pypi-smoke/data
export MISE_CACHE_DIR=/tmp/score-m5-mise/mise-state/cache
export MISE_CONFIG_DIR=/tmp/score-m6-mise/fresh-uv-pypi-smoke/mise-state/config
export MISE_STATE_DIR=/tmp/score-m6-mise/fresh-uv-pypi-smoke/mise-state/state
export MISE_SYSTEM_CONFIG_DIR=/tmp/score-m6-mise/fresh-uv-pypi-smoke/mise-state/system-config
export MISE_TRUSTED_CONFIG_PATHS="$PWD/tools/mise"
export MISE_YES=1 MISE_PYPI_UVX=true
export UV_PYTHON=/usr/bin/python3 UV_PYTHON_PREFERENCE=only-system
export UV_CACHE_DIR=/tmp/score-m5-mise/uvx-cache
export PATH=/tmp/score-m5-mise/provision-data/installs/uv/0.13.6/uv-x86_64-unknown-linux-gnu:/usr/bin:/bin
/tmp/score-m3-mise/bootstrap/mise -C tools/mise -E python install pypi:pre-commit
/tmp/score-m3-mise/bootstrap/mise -C tools/mise -E python exec -- pre-commit --version
```

The install succeeded with `uv tool install`; the execution returned
`pre-commit 4.7.0`. The `mise exec` command also populated the other selected
Python tools in that temporary data directory. The root generic Node lifecycle
retry is still needed to verify this adapter in its clean container.

## Ordinary Python dependency wheel

`tools/internal/mise/python_package.py` renders static PEP 621 extras from the
maintained `mise.native.toml`, `mise.python.toml` and Python command catalog.
The native Ruff owner supplies the `ruff` extra; the PyPI mise owner supplies
the Python-tool extras. It reads the root project's `requires-python` policy.
No version pin is maintained twice, and the wheel has no SCORE runner entry
point.

The build requires an explicit release version and package identity. The
following identity was supplied for this local candidate check only; no public
package name or release host was selected:

```console
python3 tools/internal/mise/python_package.py build \
  --output /tmp/score-m6-mise/python-dependencies-final \
  --version 0.6.1 \
  --package-name score-mise-dependencies \
  --uv /tmp/score-m5-mise/provision-bin/uv
python3 tools/internal/mise/python_package.py check \
  /tmp/score-m6-mise/python-dependencies-final
```

The generated release manifest binds the name, version, Python floor, extras,
selected tool versions, hashes of the direct owner files and the wheel digest.
The check validates that manifest and the built wheel's metadata against the
current source owners. The ordinary package build/check and
`tools/internal/mise/refresh.py` do not read or write `experiments/`.

The local consumer used the built wheel as a normal PEP 508 direct dependency:

```toml
[project]
name = "score-m6-local-wheel-consumer"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "score-mise-dependencies[ruff,pre-commit] @ file:///tmp/score-m6-mise/python-dependencies-final/dist/score_mise_dependencies-0.6.1-py3-none-any.whl",
]
```

From `/tmp/score-m6-mise/consumer-final`, these commands passed with CPython
3.12.3: `uv lock` resolved 14 packages; `uv sync` installed the local wheel,
Ruff 0.11.13 and pre-commit 4.7.0; `uv run ruff --version` and
`uv run pre-commit --version` returned those versions. This also passed:

```console
UV_PYTHON=/usr/bin/python3 /tmp/score-m5-mise/provision-bin/uvx \
  --from 'score-mise-dependencies[ruff] @ file:///tmp/score-m6-mise/python-dependencies-final/dist/score_mise_dependencies-0.6.1-py3-none-any.whl' \
  ruff --version
```

It returned `ruff 0.11.13`. uv emitted its advisory that the console script is
provided by the selected extra; the invocation completed through the local
wheel and ordinary dependency resolution.

## Maintenance ledger

| Concern | Owner and responsibility |
| --- | --- |
| Shared SCORE selection policy | `tools/environments.json` selects commands; the direct owner files carry versions. Shared link reconciliation preserves other selections and rejects untracked selected-name collisions. |
| Native manager behavior | mise resolves and installs configured backends into its data tree, supplies locked native artifacts, and reports actual install paths. Cached store content is reusable independently of exposed command membership. |
| SCORE mise adapter | `provision.py` maps selected names to owner backends/entrypoints, runs mise during provisioning, exposes direct links and maintains the per-bin ownership ledger. Before PyPI installs, it exposes the pinned mise-managed uv executable directory and explicitly selects mise's uv installer. Prepared execution continues through direct commands with the existing Bazel fallback. |
| Python compatibility and package generation | `refresh.py` exports current mise pins to existing Bazel/Python compatibility outputs. `python_package.py` builds/checks ordinary extras for local release consumption. |
| One-time migration work | M1–M5 moved callers to mise and removed the old installer. M6 adds the ownership ledger and shared-selection reconciliation. Existing untracked prefixes are not auto-migrated; first setup needs a fresh bin directory. The package generator now lives in a maintained path. |
| Recurring maintenance | Renovate updates direct mise owners and `refresh.sh` updates locks and compatibility outputs. Provisioning reconciles changed environment membership. Each local package release supplies an explicit version and package identity, then runs the maintained release check. |

## Checks and limits

These original M6 checks passed after the ownership review adjustment and
before the clean-container lifecycle exposed the uv PATH issue:

```console
python3 -m unittest tools.tests.test_mise_provision tools.tests.test_mise_python_package
/tmp/score-m5-mise/host-bin/ruff check tools/internal/mise/provision.py tools/internal/mise/python_package.py tools/internal/mise/refresh.py tools/tests/test_mise_provision.py tools/tests/test_mise_python_package.py experiments/tool-manager-mise/reference/prepare.py
/tmp/score-m5-mise/host-bin/ruff format --check tools/internal/mise/provision.py tools/internal/mise/python_package.py tools/internal/mise/refresh.py tools/tests/test_mise_provision.py tools/tests/test_mise_python_package.py experiments/tool-manager-mise/reference/prepare.py
/tmp/score-m5-mise/host-bin/buildifier -mode=check tools/BUILD.bazel
python3 tools/internal/mise/refresh.py --check
python3 tools/internal/sync_readme.py --check
PATH=/tmp/score-m5-mise/host-bin:/usr/local/bin:/usr/bin:/bin bazelisk test //tools:mise_provision_test //tools:mise_python_package_test //tools:python_tool_runner_test //tools:run_tool_test --test_output=errors
git diff --check
```

The Python unit run passed 10 tests. All four Bazel targets passed, including
the existing Python launcher and `run-tool` fallback contracts. Actual M6
provisioning reused `/tmp/score-m5-mise/provision-data` and
`/tmp/score-m3-mise/bootstrap/mise` with a fresh
`/tmp/score-m6-mise/provision-bin`; both the repository and bazel-feature
selections were already installed in that reused tree. Strict direct commands
returned uvx 0.13.6 and Starpls 0.1.22 with `PATH=/usr/bin:/bin`.

After the root lifecycle failure and fix, these current focused checks passed:

```console
python3 -m unittest tools.tests.test_mise_provision tools.tests.test_mise_python_package
/tmp/score-m5-mise/host-bin/ruff check tools/internal/mise/provision.py tools/tests/test_mise_provision.py
/tmp/score-m5-mise/host-bin/ruff format --check tools/internal/mise/provision.py tools/tests/test_mise_provision.py
PATH=/tmp/score-m5-mise/host-bin:/usr/local/bin:/usr/bin:/bin bazelisk test //tools:mise_provision_test //tools:mise_python_package_test //tools:python_tool_runner_test //tools:run_tool_test --test_output=errors
git diff --check
```

The unit command passed 11 tests; all four Bazel targets passed (the
provisioner target ran and three existing targets were cached). Ruff
check/format and the diff check passed. The fresh-data mise PyPI smoke above
installed `pre-commit 4.7.0` using the pinned cached uv and ran it through mise.

The candidate image and clean root generic Node post-create lifecycle retry
remain root-scheduled. Exact gates from the repository root are:

```console
./scripts/build.sh --amd64 score-m6-mise
docker run --rm --entrypoint /bin/bash ghcr.io/eclipse-score/devcontainer:score-m6-mise-amd64 -lc 'uv --version && uvx --version && pre-commit --version && starpls version'
devcontainer up --workspace-folder "$PWD" --config .devcontainer/devcontainer.json
devcontainer exec --workspace-folder "$PWD" --config .devcontainer/devcontainer.json bash -lc 'uv --version && uvx --version && pre-commit --version && uvx --from "codespell==2.4.1" codespell --version'
```

No ARM Linux or macOS command execution was run. Nothing was published,
registered, committed or pushed.
