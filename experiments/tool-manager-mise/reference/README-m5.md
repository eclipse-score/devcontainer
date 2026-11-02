<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Mise M5: retire the replaced installers

M5 moves native and Python command setup to a direct, install-once mise path.
Feature images and the repository post-create hook install their selected tools
from the production owner files, then expose the executables directly. The
repository DevContainer uses the generic JavaScript Node image, so its
post-create hook now provisions the repository selection itself before
registering pre-commit hooks.

## Removal and caller ledger

| Removed responsibility | Migrated caller or replacement |
| --- | --- |
| Native URL download, checksum, archive extraction, install and fallback engine in `tools/internal/devcontainer/install.py` | `tools/internal/mise/provision.py` reads the selected native owner, runs the pinned manager at setup time, and links the installed executable. |
| `uv tool install` Python path and `install-python` CLI | The same provisioner installs the exact PyPI entries in `tools/mise/mise.python.toml`. Ordinary uv/uvx users and the existing Bazel Python targets remain supported. |
| Prepared-selection handoff manifest, validation and production handoff script | Feature Dockerfiles and repository post-create call the provisioner directly. Default images need no separately generated manifest. |
| Old JSON native lock updater and its updater test | `tools/internal/mise/refresh.py` exports selected mise lock artifacts to the existing portable Bazel lock metadata. |
| Strict host `run-tool` forcing every call through Bazel | Strict host mode now executes a provisioner-created mise symlink directly and falls back to Bazel only when that link is absent. |

APT, npm, lifecycle hooks, provider metadata, external complex-tool features,
and OS package checks remain in their appropriate existing paths. The existing
`tools/run-tool` direct-command behavior and missing-command/Bazel fallback are
preserved; `//tools:run_tool_test` still covers both. No Bazel labels were added
for M5; existing native labels remain compatible.

## Owner and maintenance ledger

- `tools/mise/mise.native.toml`, `mise.python.toml`, and `mise.published.toml`
  own the selected versions. The native and published lock files are resolved
  asset metadata. `tools/score_tools/python_tools.bzl` keeps Python package,
  entrypoint and description metadata; its versions are exported from the PyPI
  mise owner.
- `tools/internal/mise/bootstrap.sh` installs a pinned, checksum-verified mise
  binary outside the command path. `provision.py` is the setup-time adapter from
  environment membership to mise backends and executable names. A prepared
  shell command invokes its linked executable directly without mise or Bazel.
- Shared policy covers ordinary Aqua, GitHub and PyPI backend installs. The
  adapter retains tool-specific executable names such as `uvx` from the `uv`
  install. APM retains its complete extracted runtime tree; OpenCode is linked
  as a direct binary. Neither gets a new M5 Bazel label or packaging path.
- A one-time migration moved feature setup and root post-create callers, deleted
  the old install engine and obsolete handoff complexity, and moved the
  production refresh/export implementation out of `experiments/`.
- Recurring version updates use Renovate's native mise manager for the live TOML
  owners. No custom regex or Aqua Renovate manager is needed. `experiments/**` is
  excluded from updater discovery.
  Renovate's post-upgrade task runs `tools/internal/mise/refresh.sh`, which
  refreshes owner locks, compatibility outputs and the generated README.
- Python versions remain in one mise owner. PEP 621 supports dependency groups,
  but no Python owner was moved under `tools/`: the root `pyproject.toml` holds
  package metadata, and the ordinary release pyproject is a local generated
  fixture. This avoids a second Python version owner.
- Local ordinary package and release generation remain in
  `experiments/tool-manager-mise/reference/prepare.py`; they are not production
  provisioning or version owners.

The update setup follows Renovate's documented mise file patterns and backend
support for Aqua, GitHub and PyPI sources
([mise manager](https://docs.renovatebot.com/modules/manager/mise/)).
Renovate's PEP 621 manager supports PEP 735 dependency groups
([PEP 621 manager](https://docs.renovatebot.com/modules/manager/pep621/)).

## Final checks

| Command or check | Result |
| --- | --- |
| `MISE_BINARY=/tmp/score-m3-mise/bootstrap/mise tools/internal/mise/refresh.sh` | Passed: refreshed all native owner locks, exported compatibility metadata and synchronized `tools/README.md`. |
| `python3 tools/internal/mise/refresh.py --check` and `python3 tools/internal/sync_readme.py --check` | Passed: owner exports and README are current. |
| `python3 -m unittest tools.tests.test_mise_provision tools.tests.test_catalog` | Passed: 18 tests. |
| `PATH=/tmp/score-m5-mise/host-bin:/usr/local/bin:/usr/bin:/bin bazelisk test //tools:python_tool_runner_test //tools:run_tool_test //tools:mise_provision_test --test_output=errors` | Passed: all 3 Bazel tests, including Python argument/cwd/exit contracts and the existing `run-tool` fallback. |
| `PATH=/tmp/score-m5-mise/host-bin:/usr/local/bin:/usr/bin:/bin bazelisk test //tools:run_tool_test --test_output=errors` | Passed after the final strict-host change. The test checks provisioned-direct vs arbitrary PATH, cwd, arguments, direct exit status, missing-link Bazel fallback and missing-Bazel failure. |
| Ruff check and format check on the changed Python files | Passed. |
| Buildifier check on `tools/BUILD.bazel`, existing `.bzl` files and generated Python catalog | Passed. |
| ShellCheck on post-create, feature installers, build script and mise scripts | Passed. |
| `actionlint .github/workflows/daily.yml`; `yamlfmt -lint .github/workflows/daily.yml` | Passed. |
| `node /home/alex/.npm/_npx/05eeecd92f4e18e0/node_modules/renovate/dist/config-validator.js .github/renovate.json5` | Passed on the final configuration using the cached Renovate package; it warned that RE2 fell back to RegExp and suggested the existing `config:base` migration. |
| `MISE_BINARY=/tmp/score-m3-mise/bootstrap/mise SCORE_MISE_REFERENCE_STATE=/tmp/score-m5-mise/release-state SCORE_MISE_DATA_DIR=/tmp/score-m5-mise/provision-data python3 experiments/tool-manager-mise/reference/prepare.py /tmp/score-m5-mise/release-m5-verified --version 0.6.1` | Passed once, creating the local package/release context. After production export code moved, `python3 experiments/tool-manager-mise/reference/prepare.py --help` and reuse of that context with `--root check` passed; no second large context was copied. |
| Host repository provision followed by direct `pre-commit`, `uvx`, and `uvx --from 'codespell==2.4.1' codespell` execution | Passed: pre-commit 4.7.0, uvx 0.13.6, codespell 2.4.1. |
| `python3 tools/internal/mise/provision.py repository --data-dir /tmp/score-m5-mise/provision-data --bin-dir /tmp/score-m5-mise/host-bin --mise /tmp/score-m3-mise/bootstrap/mise` | Passed idempotently, reusing the installed data tree; created the persistent direct command links. |
| `HOME=/tmp/score-m5-mise/user-home python3 tools/internal/mise/provision.py repository --mise /tmp/score-m5-mise/user-home/.local/share/score-tools/mise/mise --data-dir /tmp/score-m5-mise/user-home/.local/share/score-tools/mise-data --bin-dir /tmp/score-m5-mise/user-home/.local/bin` | Passed idempotently. The user-level data path reused the existing `/tmp/score-m5-mise/provision-data` payload via symlink; the manager path reused the existing pinned binary, so no large tool or manager copy was made. |
| `HOME=/tmp/score-m5-mise/user-home PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host tools/run-tool --strict uvx --version` and the same command for `pre-commit --version` | Passed: strict mode found `$HOME/.local/bin` directly without `SCORE_TOOLS_BIN_DIR` or Bazel. |
| `HOME=/tmp/score-m5-mise/user-home PATH=/tmp/score-m5-mise/user-home/.local/bin:/usr/bin:/bin uv --version`, `uvx --version`, and `uvx --from 'codespell==2.4.1' codespell --version` | Passed in a subsequent shell using the persistent user-level links: uv/uvx 0.13.6 and codespell 2.4.1. |
| `PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host SCORE_TOOLS_BIN_DIR=/tmp/score-m5-mise/provision-bin tools/run-tool --strict shellcheck --version` (also starpls, uvx, APM, OpenCode and codespell) | Passed with Bazel absent from PATH; direct outputs were ShellCheck 0.10.0, starpls 0.1.22, uvx 0.13.6, APM 0.35.0, OpenCode 2.2.3 and codespell 2.4.1. |
| `PATH=/tmp/score-m5-mise/provision-bin:/usr/bin:/bin uv --version`; `uvx --version`; `uvx --from 'codespell==2.4.1' codespell --version` | Passed in a later shell using the same persistent install tree: uv/uvx 0.13.6 and codespell 2.4.1. |

The focused static checks were run with these exact commands:

```console
/tmp/score-m5-mise/host-bin/ruff check tools/internal/mise/refresh.py tools/internal/mise/provision.py tools/internal/devcontainer/install.py tools/score_tools/catalog.py tools/tests/test_mise_provision.py experiments/tool-manager-mise/reference/prepare.py experiments/tool-manager-mise/reference/provision.py
/tmp/score-m5-mise/host-bin/ruff format --check tools/internal/mise/refresh.py tools/internal/mise/provision.py tools/internal/devcontainer/install.py tools/score_tools/catalog.py tools/tests/test_mise_provision.py experiments/tool-manager-mise/reference/prepare.py experiments/tool-manager-mise/reference/provision.py
/tmp/score-m5-mise/host-bin/buildifier -mode=check tools/BUILD.bazel tools/python_tool.bzl tools/multitool.bzl tools/score_tools/python_tools.bzl tools/lockfiles/python_tools.bzl
/tmp/score-m5-mise/host-bin/shellcheck .devcontainer/post_create_command.sh src/s-core-devcontainer/.devcontainer/s-core-local/install.sh src/s-core-devcontainer/.devcontainer/bazel-feature/install.sh scripts/build.sh tools/internal/mise/bootstrap.sh tools/internal/mise/refresh.sh
/tmp/score-m5-mise/host-bin/shellcheck tools/run-tool tools/tests/run_tool_test.sh
/tmp/score-m5-mise/host-bin/actionlint .github/workflows/daily.yml
/tmp/score-m5-mise/host-bin/yamlfmt -lint .github/workflows/daily.yml
npx --yes --package renovate renovate-config-validator .github/renovate.json5
git diff --check
```

The direct strict-host commands run with Bazel absent from `PATH` were:

```console
PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host SCORE_TOOLS_BIN_DIR=/tmp/score-m5-mise/provision-bin tools/run-tool --strict shellcheck --version
PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host SCORE_TOOLS_BIN_DIR=/tmp/score-m5-mise/provision-bin tools/run-tool --strict starpls version
PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host SCORE_TOOLS_BIN_DIR=/tmp/score-m5-mise/provision-bin tools/run-tool --strict uvx --version
PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host SCORE_TOOLS_BIN_DIR=/tmp/score-m5-mise/provision-bin tools/run-tool --strict apm --version
PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host SCORE_TOOLS_BIN_DIR=/tmp/score-m5-mise/provision-bin tools/run-tool --strict opencode --version
PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host SCORE_TOOLS_BIN_DIR=/tmp/score-m5-mise/provision-bin tools/run-tool --strict codespell --version
```

The user-level path was also executed with `$HOME/.local/bin` discovery and
subsequent ordinary uv/uvx commands:

```console
HOME=/tmp/score-m5-mise/user-home PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host tools/run-tool --strict uvx --version
HOME=/tmp/score-m5-mise/user-home PATH=/usr/bin:/bin RUN_TOOL_CONTAINER_MODE=host tools/run-tool --strict pre-commit --version
HOME=/tmp/score-m5-mise/user-home PATH=/tmp/score-m5-mise/user-home/.local/bin:/usr/bin:/bin uv --version
HOME=/tmp/score-m5-mise/user-home PATH=/tmp/score-m5-mise/user-home/.local/bin:/usr/bin:/bin uvx --version
HOME=/tmp/score-m5-mise/user-home PATH=/tmp/score-m5-mise/user-home/.local/bin:/usr/bin:/bin UV_CACHE_DIR=/tmp/score-m5-mise/user-uvx-cache uvx --from 'codespell==2.4.1' codespell --version
```

Earlier M5 provisioning runs installed the `s-core-local` and `bazel-feature`
profiles into isolated `/tmp/score-m5-mise` prefixes and directly executed the
selected native and Python commands, including APM 0.35.0, OpenCode 2.2.3,
starpls 0.1.22, codespell 2.4.1, and the retained uv/uvx consumers. A local
release was generated once; it was not copied again after the exporter moved.
The final release input check reused that context and passed.

## Platform and image limits

The actual runtime provisioning and execution evidence is Linux amd64 only.
Native lock declarations include Linux amd64, Linux arm64 and macOS arm64;
APM and OpenCode additionally declare macOS x64. Those other platform entries
were exported but were not executed here.

The documented user-level setup uses persistent `$HOME/.local/share/score-tools`
and `$HOME/.local/bin` paths. The `HOME=/tmp/score-m5-mise/user-home` commands
above exercised that exact path layout with reused data and manager links. Add
`$HOME/.local/bin` to the user's shell startup for later ordinary `uv` and
`uvx` calls.

No full image build was attempted. Disk had about 4.5 GiB free and image
scheduling belongs to the root comparison owner. The exact candidate build
command is `./scripts/build.sh --amd64 score-m5-mise`, which produces
`ghcr.io/eclipse-score/devcontainer:score-m5-mise-amd64`.
