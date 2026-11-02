<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Aqua M6 handoff

**Status: stable source ready; Aqua published image retry pending.** Shared HEAD remains `2e337e4`; inherited M1–M5 changes remain present. All three generic Node lifecycle gates passed; Nix and Mise full builds plus feature suites passed. Root is retrying the Aqua image after the executable-mode fix. No commit or publication was performed.

## Source maintenance ledger

| Layer | Maintained responsibility |
| --- | --- |
| Shared SCORE policy | `tools/owners/aqua/aqua.yaml` owns native versions/tags; `tools/owners/aqua/pyproject.toml` owns Python versions/groups. `python_package.py` derives standard extras, and release version/package identity are required CLI inputs. |
| Aqua and uv behavior | Aqua selects/copies native tools; uv installs Python distributions. The host provisioner tracks each exposed command by profile, stages uv entrypoints, retains cross-profile shared names, removes unchanged stale exposures, and refuses collisions with foreign or modified commands. |
| SCORE adapters | `tools/score_tools/python_tools.bzl` records public command identities including secondary entrypoints; `export_native.py` keeps existing Bazel portable URL/hash/layout contracts; APM retains its adjacent runtime tree. |
| Local release/check | `prepare_dependency_release.py` builds a local wheel and owner/selection manifest; `check_dependency_release.py` exercises standard uv/uvx consumers. No SCORE wrapper, credentials, hosting policy, or publishing flow is needed or selected. |
| One-time migration | A prefix without a supported ownership ledger must be replaced with a fresh `--prefix`; the provisioner never guesses prior ownership. |
| Recurring maintenance | Run `refresh_owners.py`, then `sync_repository.py --check` and `sync_readme.py --check`; reprovision a managed prefix after selection changes. |

The ordinary and proxy Dockerfiles also install distro `python3` in the
existing CA-refresh APT step before the Python-based image bootstrap. The
cached `buildpack-deps:noble-curl` base lacked Python, while all other direct
commands needed at this boundary were already present. This uses the distro's
current APT package without adding a tool-version pin or invoking an old
installer command; tool version owners remain unchanged. See the candidate
README's **Early image bootstrap** section for the exact bounded container
check, which installed only `ca-certificates` and `python3`, observed Python
3.12.3, and started each bootstrap/provider CLI without downloading tool
payloads.

The Aqua published image gate then found that `provision_image_tools.sh` was
called directly by both Dockerfiles but had mode `100644`. Its mode is now
`100755`; script contents and behavior are unchanged. Nearby direct shebang
entrypoints were audited and already executable, while Python helpers run via
`python3`. Focused pre-commit shebang checks, `bash -n`, and ShellCheck pass.
The root-owned full image retry is the only remaining integration gate; exact
commands and evidence are in the candidate README.

The earlier generic Node terminal failure exposed that prepared tools were
provisioned under `/home/node/.local/share/score-tools` but omitted from a new
terminal's PATH. The candidate config now explicitly selects the existing Node
image's remote user (`node`) and exports that user's direct bin directory in
`remoteEnv`, aligned with the post-create prefix. Root reports all three generic
Node lifecycle gates passed, including the actual terminal lookup.

The real-manager deselection reprovision is now complete under
`/tmp/score-m6-aqua/prefix-real-reconcile`. I copied the Aqua owner directory,
initially provisioned the real repository profile with Aqua 2.65.2 and uv
0.13.6 from the M5 Aqua/uv caches (`UV_OFFLINE=1`), then removed only the
repository tag for buildifier and actionlint in that copy and ran the same
maintained CLI again. It reported `retired_commands: ["buildifier"]`; the
changed actionlint executable and an unrelated sentinel both remained. The
retained repository commands ran at their pinned versions: Bazelisk 1.27.0,
pre-commit 4.7.0, Ruff 0.11.12, ShellCheck 0.10.0, uv/uvx 0.13.6, and yamlfmt
0.17.0. The prefix apparent size was 116,326,719 bytes (<150,000,000). Exact
commands and the evidence boundary are recorded in README-m6.md. Aqua and uv
materialized selected commands from the reused M5 caches; the M5 prepared
host-tools tree was not bulk-copied.

The earlier fake-manager fixture remains fixture-only evidence for
cross-profile repository/published sharing, Python alias sharing/retirement,
and broader foreign/symlink cases. The actual run provisioned only the
repository profile; no published/APM run, container, image build, or source
change was part of this real-manager check.

## Exact checks and results

- `python3 -m unittest tools.tests.test_provision_host_tools tools.tests.test_aqua_python_package` — **10 passed**.
- Ruff check and `ruff format --check` on the nine changed Python files — **passed**; all files formatted.
- Python syntax: `python3 -m py_compile tools/internal/aqua/python_package.py tools/internal/aqua/prepare_dependency_release.py tools/internal/aqua/check_dependency_release.py tools/internal/aqua/sync_repository.py tools/internal/devcontainer/provision_host_tools.py tools/tests/test_provision_host_tools.py tools/tests/test_aqua_python_package.py experiments/tool-manager-aqua/reference/prepare.py experiments/tool-manager-aqua/reference/check.py` — **exit 0**.
- `python3 tools/internal/aqua/sync_repository.py --check` — **exit 0, `changed: []`**.
- `python3 tools/internal/sync_readme.py --check` — **exit 0**.
- `git diff --check` — **exit 0**.
- `docker buildx build --check --platform linux/amd64 -f src/s-core-devcontainer/.devcontainer/Dockerfile .` and the same command with `-f src/s-core-devcontainer/.devcontainer/with-proxy-vars.Dockerfile` — **both passed with no warnings**; no layers were built.
- `bash -n tools/internal/devcontainer/provision_image_tools.sh` and `/tmp/score-m5-aqua/host-tools/bin/shellcheck tools/internal/devcontainer/provision_image_tools.sh` — **both passed**.
- Cached-base Python bootstrap check — **passed**, as detailed in `experiments/tool-manager-aqua/reference/README-m6.md`; no full image or Aqua/uv payload provisioning was run.
- Generic Node lifecycle follow-up — **all three actual lifecycle gates passed**, including direct terminal tool lookup. Root has confirmed the updated user home/PATH configuration.
- Aqua published image — the prior gate failed at Dockerfile line 46 because `provision_image_tools.sh` was mode `100644`; changed the direct shebang helper to executable mode `100755` without changing script content. Both shebang pre-commit hooks, `bash -n`, and ShellCheck passed. Root owns the full image retry.
- Real Aqua/uv repository reprovision — **passed** using the maintained provisioner twice on `/tmp/score-m6-aqua/prefix-real-reconcile`, with actual Aqua 2.65.2, actual uv 0.13.6, and `UV_OFFLINE=1`. It retired unchanged owned `buildifier`, retained user-replaced deselected `actionlint` plus the unrelated sentinel, and executed the remaining pinned repository commands. Prefix apparent size was 116,326,719 bytes. See README-m6.md for commands and outputs.
- Cross-profile repository/published retention, Python alias sharing/retirement, and extra symlink/foreign replacement cases remain fake-manager fixture-only; no real published/APM profile was provisioned.
- `python3` JSONC configuration assertions — **passed**: explicit remote user, direct prepared bin PATH, and `$HOME`-based post-create prefix agree.
- Fresh interactive Bash PATH simulation using temporary symlinks to the M5 cached uv binaries — **passed**: `type -P uv` and `type -P uvx` resolved under the simulated user's `.local/share/score-tools/bin`; both reported `0.13.6`. The later actual generic Node lifecycle gates also passed.
- `python3 /tmp/score-m6-aqua/reconcile_fixture.py` — **passed**. Its Aqua/uv test doubles exercised same-prefix repository/published sharing, current-prefix reuse, command retirement, Python aliases, and preservation of foreign/user-replaced commands.
- Real uv script staging with the M5 cache:

  ```console
  UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host UV_TOOL_BIN_DIR=/tmp/score-m6-aqua/uv-stage/exposure UV_TOOL_DIR=/tmp/score-m6-aqua/uv-stage/tools UV_PYTHON_INSTALL_DIR=/tmp/score-m6-aqua/uv-stage/python UV_PYTHON_DOWNLOADS=never /tmp/score-m5-aqua/host-tools/bin/uv --no-config tool install --force pytest==9.0.2
  ```

  **Exit 0:** uv reported `Installed 2 executables: py.test, pytest`.
- Built the local wheel with explicit inputs:

  ```console
  UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host UV_PYTHON_DOWNLOADS=never UV_BINARY=/tmp/score-m5-aqua/host-tools/bin/uv python3 tools/internal/aqua/prepare_dependency_release.py --output /tmp/score-m6-aqua/release --version 0.4.0 --package-name score-aqua-m6-local
  ```

  **Exit 0:** `score_aqua_m6_local-0.4.0-py3-none-any.whl`, SHA-256 `d0449b5c8526945ffc730e41079ab4d4ef9c00e7ccd2d022a1bb318449c73ec0`.
- Checked the local wheel with direct uv and uvx clients:

  ```console
  UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host UV_PYTHON_DOWNLOADS=never UV_BINARY=/tmp/score-m5-aqua/host-tools/bin/uv UVX_BINARY=/tmp/score-m5-aqua/host-tools/bin/uvx python3 tools/internal/aqua/check_dependency_release.py /tmp/score-m6-aqua/release /tmp/score-m6-aqua/wheel-check-m6
  ```

  **Exit 0:** `uv add`, `uv lock`, `uv sync --locked`, `uv run --locked ruff --version`, and `uvx --with <local wheel> ruff --version` all resolved Ruff `0.11.12`. The consumer lock records the wheel path.
- `rg` production-path audit returned no matches for `experiments/`, `generated-package.toml`, or experiment release/check scripts under maintained Aqua/provisioner paths.

Exact Ruff commands:

```console
/tmp/score-m5-aqua/host-tools/bin/ruff check \
  tools/internal/aqua/python_package.py \
  tools/internal/aqua/prepare_dependency_release.py \
  tools/internal/aqua/check_dependency_release.py \
  tools/internal/aqua/sync_repository.py \
  tools/internal/devcontainer/provision_host_tools.py \
  tools/tests/test_provision_host_tools.py \
  tools/tests/test_aqua_python_package.py \
  experiments/tool-manager-aqua/reference/prepare.py \
  experiments/tool-manager-aqua/reference/check.py

/tmp/score-m5-aqua/host-tools/bin/ruff format --check \
  tools/internal/aqua/python_package.py \
  tools/internal/aqua/prepare_dependency_release.py \
  tools/internal/aqua/check_dependency_release.py \
  tools/internal/aqua/sync_repository.py \
  tools/internal/devcontainer/provision_host_tools.py \
  tools/tests/test_provision_host_tools.py \
  tools/tests/test_aqua_python_package.py \
  experiments/tool-manager-aqua/reference/prepare.py \
  experiments/tool-manager-aqua/reference/check.py
```

## Remaining root-owned gate

All three generic Node lifecycle gates and the Nix/Mise full builds plus feature suites passed. Root is retrying the Aqua published image build; the Aqua worker did not run a full image build.

```console
npm exec --yes --package=@devcontainers/cli -- devcontainer build \
  --workspace-folder src/s-core-devcontainer \
  --image-name score-aqua-m6:linux-amd64 \
  --platform linux/amd64
```

Root owns the retry and final aggregate review. See `experiments/tool-manager-aqua/reference/README-m6.md` for the full candidate report and historical M5 direct/Bazel evidence.

## Aqua default-inventory command exposure

The full image log showed APT `gh` `2.45.0-1ubuntu0.3` matching its
owner-derived compatibility version, while Aqua's published `uv` copy also
returned `cli/cli`'s `gh` v2.102.0. The image prepends its direct-tool bin to
PATH, so this unselected Aqua output shadowed the intended APT provider. The
feature assertion is restored to its original unqualified `gh --version`
check.

The maintained provisioner now derives selected native command names from the
current Aqua owner profile, passes those names to `aqua cp`, and directs output
to a private temporary directory. It validates that each selected executable
exists before moving only those selected paths into the shared prefix. Extra
outputs such as `gh` remain private. The existing foreign/user replacement
guard and APM runtime copy remain in place. Aqua 2.65.2 `cp --help` confirms
command-name selection is supported; an actual cached `uv uvx` copy and the
full repository selection both worked.

New unit regressions use Aqua `cp` emitting an extra `gh`. They verify that a
fresh prefix has no `gh`, a foreign `gh` sentinel is preserved, selected tools
are executable, missing selected output fails, and a deselected owned command
is retired. `python3 -m unittest tools.tests.test_provision_host_tools
tools.tests.test_aqua_python_package` passed all 13 tests. Targeted Ruff check,
Ruff format check, Python compilation, and `git diff --check` passed. The
feature shell test remains unchanged from its original unqualified command.

The corrected maintained CLI passed a real cached-manager reprovision on fresh
`/tmp/score-m6-aqua/prefix-exposure-fix`: Aqua 2.65.2 and uv 0.13.6 ran using
the existing M5 caches. Removing only buildifier's repository tag in a copied
owner caused the real same-prefix run to report `retired_commands:
["buildifier"]`. The official owner was then restored. The final `bin` exactly
matched the owner-selected repository commands (`actionlint`, `bazelisk`,
`buildifier`, `pre-commit`, `ruff`, `shellcheck`, `uv`, `uvx`, and `yamlfmt`),
had no `gh`, and each command ran its version check at the owner pin. `du -sh`
reported 125 MiB. This fresh prefix is available for root runtime checks.

No image was built here. Root owns the actual fresh full-image retry and
aggregate review; the final source-ready marker is
`/tmp/score-m6-aqua/aqua.exposure-fix.last.md`.

## Final filesystem mode sweep

Normalized the nine requested Python shebang tools/tests plus three additional
round2/round3 fixture shebang files found by the independent on-disk audit to
mode `100755`. The earlier `provision_image_tools.sh` fix remains `100755`.
Both repository shebang/executable pre-commit hooks passed across all affected
paths, and the filesystem audit reports zero shebang/mode violations. No file
contents changed in this cleanup; no tests, builds, staging, or commits were
run.
