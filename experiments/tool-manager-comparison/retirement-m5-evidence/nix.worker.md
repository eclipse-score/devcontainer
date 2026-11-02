<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Nix M5: production ownership and installer retirement

Status as of 2026-11-02. This candidate moves the native and Python command
selection to a production Nix flake, provisions the root generic Node
devcontainer from post-create, and removes the replaced native/Python
installation engines from `install.py`. The earlier M1–M4 reports remain
historical evidence; `tools/nix/` and `tools/internal/nix/` are the live paths.

## Maintenance ledger

| Responsibility | Production owner | Routine maintenance |
| --- | --- | --- |
| Package versions and profile membership | `tools/nix/flake.nix`, `flake.lock`, and `opencode-hashes.json` | Update the Nix input lock or exact `opencodeVersion`; refresh the OpenCode asset hashes through the exporter. `published` contains all 15 tools; `repository` contains the established nine commands. |
| Host development profile | `tools/nix/install-host.sh` | Root `.devcontainer/post_create_command.sh` bootstraps single-user Nix when absent, adds or upgrades the `path:${FLAKE}#repository` profile, and exposes it in `.profile`, `.bashrc`, and the current lifecycle shell. Prepared `tools/run-tool` calls exec the profile command directly. |
| Image runtime | `tools/internal/nix/prepare.py`, `tools/internal/nix/sync.py`, and the feature Dockerfiles | Build an immutable Nix closure at preparation time; generated activation links selected executables directly into `/usr/local/bin`. Runtime tool calls need no Nix or Bazel resolver. |
| Existing Bazel and catalog interfaces | `tools/internal/nix/sync.py` | Regenerate native lockfiles, Python package versions, repository membership, and the generated tool overview from the Nix owner. The portable release hashes remain the rules_multitool adapter; they are not image installers. |
| OS and external providers | `tools/internal/devcontainer/install.py` and feature lifecycle scripts | Keep APT/npm installation, feature build/cleanup phases, and provider-specific lifecycle setup here. Native and Python commands come from the Nix profile. |
| Dependency refresh | `.github/renovate.json5`, `.github/workflows/daily.yml`, and `.github/renovate-entrypoint.sh` | Renovate's Nix manager updates the live flake and lock. One exact-release matcher updates OpenCode's derivation version; post-upgrade sync refreshes compatibility hashes and the tool overview. `experiments/**` is ignored so historical snapshots are not extra owners. |

The pinned nixpkgs revision is `1c89083e451e891152365b799595cf7790a43325`.
APM uses `pkgs.apm-cli`, preserving the complete runtime tree. OpenCode is an
exact 2.2.3 release-asset derivation with Linux runtime patching and generated
hashes for Linux amd64, Linux arm64, and macOS arm64. Its source selection stays
at 2.2.3 until an intentional dependency refresh.

The Nix Renovate manager is currently documented as beta and requires explicit
opt-in; this configuration enables it for the live flake only. See the
[Renovate Nix manager documentation](https://docs.renovatebot.com/modules/manager/nix/).

## Retired code and preserved interfaces

- `install.py` no longer downloads, hashes, extracts, or installs native
  binaries, and no longer invokes `uv tool install` for Python commands.
- The `install` and `install-python` subcommands, prepared-tools manifest
  validation, and installer handoff/fallback branches are removed. The old
  runtime handoff is not needed by the image activation links.
- Feature and root repository setup still applies APT/npm providers. The root
  generic Node devcontainer installs the repository Nix profile before calling
  `pre-commit install`; its shell startup files retain the profile PATH for
  later terminals.
- The public `//tools:NAME` native labels and the ordinary uv/uvx Python
  launcher remain. Non-strict unprepared callers keep their PATH route. When a
  prepared host pin or container command is missing, `run-tool` still uses the
  existing Bazel fallback when Bazel is available.

## Maintenance boundary

- The one-time migration moved the live owner and producer/exporter into
  `tools/nix/` and `tools/internal/nix/`, moved both features' native/Python
  runtime delivery and root post-create provisioning to prepared Nix profiles,
  and deleted the native download/extract and Python uv-tool install engines
  from `install.py`. Feature `environment` calls remain for APT/npm providers
  and build/cleanup lifecycle work.
- The compatibility exporter remains shared policy for public Bazel labels:
  Nix supplies selected versions and membership, while the existing portable
  URL/hash/archive-layout format remains generated output for
  `rules_multitool`. Release-asset hashes are not Nix store hashes.
- Retained tool-specific package work is bounded: `pkgs.apm-cli` supplies
  APM's complete runtime tree; OpenCode uses the exact 2.2.3 release binary,
  platform hashes and Linux runtime patching. A source-build fallback is not
  part of the required runtime path.
- Recurring maintenance uses Renovate's built-in `nix` manager for the live
  flake input and lock. One exact-release regex updates `opencodeVersion`,
  which is outside ordinary flake-input updates. The allowed post-upgrade
  exporter refreshes Bazel/Python compatibility metadata and the generated
  overview. Image closure preparation and host profile upgrade happen during
  their normal build/post-create lifecycles; ordinary tool execution adds no
  manager lookup.

## Maintainer commands

From the worktree root:

```sh
python3 tools/internal/nix/sync.py
python3 tools/internal/sync_readme.py
python3 tools/internal/nix/sync.py --check --release /path/to/release --system x86_64-linux
tools/nix/install-host.sh
bazel test //tools:run_tool_test //tools:python_tool_runner_test
```

`scripts/build.sh` creates a fresh local Nix runtime automatically when
`SCORE_NIX_PREPARED_RELEASE` is unset. `scripts/publish.sh` uses the same path
and only pushes when deliberately invoked with the publication workflow; no
publication was run for this candidate.

## Current checks

- Nix exporter and release check passed:
  `python3 tools/internal/nix/sync.py --check --release /tmp/score-m5-nix/release-amd64 --system x86_64-linux`
  reported `Stale outputs:` empty. It evaluated x86_64-linux,
  aarch64-linux, and aarch64-darwin and confirmed that versions and profile
  membership agree across all three.
- The current production owner evaluates to the same published store profile
  path recorded by `/tmp/score-m5-nix/release-amd64/release.json`. From that
  exact path, APM 0.35.0, OpenCode 2.2.3, basedpyright 1.39.8, Codespell 2.4.3,
  pytest 9.1.1, and pre-commit 4.7.0 were executed. The Bazelisk version probe
  is skipped by the Nix producer because that command starts Bazel. The M5
  Linux amd64 release was checked against the relocated production flake; it
  is not an M1–M4 runtime.
- The production host helper was run against the current copied owner in the
  existing Nix producer container. `nix profile add` created a profile from
  `path:/tmp/score-nix-m5-host-workspace/tools/nix#repository`, a second helper
  run upgraded that same stored path reference, and `run-tool --strict`
  directly executed pre-commit 4.7.0, uv 0.13.5, and uvx 0.13.5. A later
  interactive shell resolved uv and uvx from that profile.
- The isolated root post-create fixture passed with a fake Nix bootstrap. It
  verified APT/npm provider invocation order, the explicit `path:` flake
  reference, pre-commit after provisioning, builder setup last, and profile
  PATH in both the lifecycle shell and a later interactive shell. This is a
  source integration fixture, not a generic Node image test.
- `python3 -m unittest discover -s tools/tests -p 'test_*.py'`: 23 tests
  passed. Direct `run-tool` and uvx shell tests passed.
- `/home/alex/.local/bin/bazelisk --output_base=/tmp/score-m5-nix/bazel-output
  test --repository_cache=/tmp/score-m5-nix/bazel-repository-cache
  //tools:run_tool_test //tools:python_tool_runner_test --test_output=errors`:
  both Bazel targets passed (the Python runner target was served from cache).
- `python3 /tmp/score-m5-nix/verify-post-create.py`: passed against the current
  root post-create script and Nix owner, including provider ordering,
  single-user bootstrap, explicit `path:` profile add, hook setup, and PATH in
  a later interactive shell.
- ShellCheck passed for modified shell files (`shellcheck -x -P SCRIPTDIR`),
  actionlint passed for `ci.yaml`, `daily.yml`, and
  `release-and-publish.yaml`, and `tools/internal/sync_readme.py --check`,
  Python compilation, Renovate JSONC parsing, and `git diff --check` passed.
- Nix package selection was evaluated for ARM Linux and ARM macOS, but no
  commands were executed on those platforms.
- Nix evaluation emits deprecation warnings for `stdenv.isLinux` and
  `stdenv.isDarwin`; the current checked release remains aligned with these
  source files. Updating those aliases requires refreshing the recorded
  release metadata.

## Image gate still pending

No fresh M5 full image completion is claimed. The first amd64 image attempt
reached the local feature and failed because `tools/internal/devcontainer/install.py`
was missing its executable bit; that mode is now executable. The interrupted
retry did not reach a Dev Container image build. Root owns the next image gate;
do not count an earlier M3 image as current proof.

Exact command for the root-scheduled amd64 image gate, reusing the retained M5
release and candidate-specific image name:

```sh
PATH=/tmp/score-m5-nix/bin:$PATH \
SCORE_NIX_PREPARED_RELEASE=/tmp/score-m5-nix/release-amd64 \
SCORE_NIX_IMAGE_REPOSITORY=score-nix-m5 \
scripts/build.sh --amd64 m5-image
```

The expected tag is `score-nix-m5:m5-image-amd64`. The full image and its
Dev Container feature smoke test remain root-scheduled. Renovate's hosted
workflow and `renovate-config-validator` were not run locally.
