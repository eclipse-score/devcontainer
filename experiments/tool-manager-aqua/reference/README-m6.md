<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Aqua maintenance ledger — milestone 6

## Outcome

Aqua now safely reconciles commands exposed in a reused host prefix. Its
ownership state is per profile, shared commands stay while another selected
profile still owns them, and stale files are deleted only when their recorded
identity still matches. Foreign commands and user replacements remain intact.
A selected name that collides with an untracked or changed command is refused.
Prefixes without a supported ownership ledger need a fresh `--prefix`; the
provisioner does not guess ownership from names. Aqua's output is staged
privately, and only native command names selected by the current owner profile
are moved into the shared `bin` directory.

Ordinary Python dependency metadata, local wheel production, and the uv/uvx
consumer check now live under maintained `tools/internal/aqua/` paths. They read
the existing Aqua and Python owners directly. Release version and configurable
distribution identity are required inputs. The resulting wheel and manifest
bind its name, version, bytes, owner digest, and selected tool versions. Nothing
is published or registered.

Existing Bazel labels, strict direct host calls, and missing-command Bazel
fallback are unchanged. The root integration engineer owns the serial image
retry. All three generic Node lifecycle gates have passed, including the fresh
terminal's direct prepared-tool lookup. The Aqua published image retry is the
last remaining integration gate.

## Responsibility ledger

| Responsibility | Maintained owner or adapter | M6 boundary |
| --- | --- | --- |
| Native versions and environment tags | `tools/owners/aqua/aqua.yaml` | Aqua registry recipes resolve and copy selected native tools. No version list is added to the provisioner. |
| Native checksums and bootstrap | `aqua-checksums.json`, `aqua-bootstrap.toml` | Aqua checksums are refreshed by the maintained owner refresh. Bootstrap remains build/provision time. |
| Python package versions and profiles | `tools/owners/aqua/pyproject.toml` | Dependency groups remain the sole direct Python version owner. |
| Python command identities | `tools/score_tools/python_tools.bzl` | Existing identity metadata lists secondary scripts such as `py.test` and `basedpyright-langserver`; uv installs the scripts. |
| Portable Bazel URLs, hashes, and archive layouts | `tools/internal/aqua/export_native.py` | Existing bounded Multitool adapter remains necessary for public Bazel contracts; it is not a second version owner. |
| Dependency package metadata | `tools/internal/aqua/python_package.py` | Extras and selected versions derive from Aqua and Python owners. The local name and release version are command inputs. |
| Local wheel and manifest | `prepare_dependency_release.py` | Builds one ordinary wheel and records owner/selection binding. No credentials, hosting choice, or publishing step exists. |
| Normal consumer check | `check_dependency_release.py` | Uses direct `uv add`, `uv lock`, `uv sync`, `uv run`, and `uvx --with` calls against the local wheel. |
| Reused host command exposure | `tools/internal/devcontainer/provision_host_tools.py` | Stages Aqua output and exposes only current profile commands, stages Python scripts, reconciles shared membership, and protects foreign or modified paths. |
| APM package tree | `provision_host_tools.py` and image provisioning | Retains APM's complete adjacent runtime tree and exposes its executable link. |
| APT, npm, editor/runtime features | Existing providers and feature installers | Their lifecycle and complex external integrations remain with existing owners. |

The generated root lockfiles, generated Python versions, environment membership,
tool README, and release metadata are compatibility or release outputs. They
do not duplicate the version owners.

## Early image bootstrap

Both the ordinary and proxy Dockerfiles install the distro `python3` package
in the existing CA-refresh APT step, before `provision_image_tools.sh` runs.
That bootstrap is earlier than Dev Container feature installation, so feature
providers cannot supply its interpreter. APT resolves the base distribution's
Python without adding a Python version pin; native and Python tool versions
remain in the existing Aqua and Python owners. The bootstrap and provisioner
use Python's standard library only. The base already supplies the shell/core
commands used at this boundary (`bash`, `mktemp`, `chmod`, `rm`, `userdel`,
`apt-get`, and `update-ca-certificates`), and the Dockerfiles install
`ca-certificates` alongside Python before network access.

The original cached-base probe was:

```console
docker run --rm --network none --entrypoint /bin/sh buildpack-deps:noble-curl \
  -c "command -v python3 || true"
```

It printed no path. After adding `python3`, this bounded ephemeral-container
check installed only the APT bootstrap dependencies and started the three
Python scripts that run at or after this boundary. It mounted the tools tree
read-only and did not copy or install Aqua/uv tool payloads:

```console
docker run --rm --network bridge \
  --mount type=bind,source=/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/tools,target=/tmp/score-tools,readonly \
  --entrypoint /bin/sh buildpack-deps:noble-curl -c 'set -eu; if command -v python3 >/dev/null 2>&1; then echo "unexpected python3 in base image" >&2; exit 1; fi; echo "base: python3 missing as expected"; apt-get update; apt-get install -y --no-install-recommends ca-certificates python3; update-ca-certificates --fresh; python3 --version; python3 /tmp/score-tools/internal/devcontainer/bootstrap_aqua.py --help >/dev/null; python3 /tmp/score-tools/internal/devcontainer/provision_host_tools.py --help >/dev/null; python3 /tmp/score-tools/internal/devcontainer/install.py --help >/dev/null; echo "bootstrap scripts start with distro python3"'
```

It exited 0 with Python `3.12.3`; APT installed `python3` and its runtime
dependencies (24.2 MB installed), and the bootstrap, host provisioner, and
feature provider CLI entrypoints all started. The image itself was not built.

## Image bootstrap executable mode

The root-owned published Aqua image attempt reached the direct `RUN` at
Dockerfile line 46 and failed with exit 126 because
`tools/internal/devcontainer/provision_image_tools.sh` had a shebang but mode
`100644`. Both ordinary and proxy Dockerfiles call that same path directly,
so the source script now has executable mode `100755`; its contents and
behavior are unchanged. The immediate related direct entrypoints were checked:
the feature `install.sh` scripts and `.devcontainer/post_create_command.sh`
already have executable mode, and `install.py` is executable where the feature
metadata loader invokes it directly. The Python bootstrap and host provisioner
are invoked explicitly with `python3`, but their shebangs still require
executable mode under the repository hook.

Focused validation ran the repository's
`check-shebang-scripts-are-executable` and
`check-executables-have-shebangs` pre-commit hooks for the affected entrypoint
files, plus `bash -n` and ShellCheck for `provision_image_tools.sh`; all passed:

```console
pre-commit run check-shebang-scripts-are-executable --files \
  tools/internal/devcontainer/provision_image_tools.sh \
  tools/internal/devcontainer/load_feature_versions.sh \
  tools/internal/devcontainer/install.py \
  src/s-core-devcontainer/.devcontainer/bazel-feature/install.sh \
  src/s-core-devcontainer/.devcontainer/s-core-local/install.sh \
  .devcontainer/post_create_command.sh
pre-commit run check-executables-have-shebangs --files \
  tools/internal/devcontainer/provision_image_tools.sh \
  tools/internal/devcontainer/load_feature_versions.sh \
  tools/internal/devcontainer/install.py \
  src/s-core-devcontainer/.devcontainer/bazel-feature/install.sh \
  src/s-core-devcontainer/.devcontainer/s-core-local/install.sh \
  .devcontainer/post_create_command.sh
bash -n tools/internal/devcontainer/provision_image_tools.sh
/tmp/score-m5-aqua/host-tools/bin/shellcheck \
  tools/internal/devcontainer/provision_image_tools.sh
```

No Dockerfile behavior or bootstrap dependencies changed in this fix. The root
integration engineer owns the published image retry.

The final filesystem audit found nine additional shebang Python tools/tests
and three round2/round3 fixture scripts that also needed mode `100755`. Those
and `provision_image_tools.sh` now pass both shebang/executable hooks; a
workspace filesystem audit reports zero shebang/mode violations. File contents
were unchanged.

## Default-inventory command exposure

The Aqua image gate correctly found a provider collision: the published Aqua
copy for `uv` also returned `cli/cli`'s `gh`, although `gh` is absent from the
selected Aqua owner inventory and is provided by APT. Since the image places
the direct-tool prefix first on `PATH`, that extra Aqua file shadowed the
intended APT command and failed the existing unqualified compatibility check.
The feature test remains unqualified and keeps its owner-derived APT version
expectation.

Aqua 2.65.2's `cp --help` supports explicit command names. The provisioner now
passes the sorted names selected from the current profile in
`tools/owners/aqua/aqua.yaml` (including the `uvx` command), directs `cp` to a
private temporary directory, verifies that every selected executable exists,
then moves only those selected files into `prefix/bin`. Any additional Aqua
output remains private and is discarded. This uses the existing owner list,
adds no blacklist or pin, retains the APM runtime copy, and runs the existing
foreign/user replacement guard before exposure. A missing selected file fails
provisioning before any selected file is moved.

The Aqua feature assertion was restored to its original unqualified
`gh --version` form. New provisioner regressions use an Aqua `cp` double that
emits an extra `gh`: a fresh prefix receives no `gh`, a foreign `gh` sentinel
is unchanged, selected tools remain executable, a deselected owned command is
retired, and missing selected output is rejected. The existing ownership guard
and reconciliation tests continue to cover user replacements and sharing.

The corrected maintained provisioner also passed a bounded actual-manager
smoke on fresh `/tmp/score-m6-aqua/prefix-exposure-fix` with cached Aqua 2.65.2
and uv 0.13.6 (`UV_OFFLINE=1`). The first pass used the current repository
owner. A copied owner then removed only buildifier's repository tag; the real
same-prefix rerun reported `retired_commands: ["buildifier"]`. The official
owner was restored for the final pass. Its `bin` exactly matched the selected
repository native/Python command set, had no `gh`, and all nine commands ran
their version commands at the owner pins. `du -sh` reported 125 MiB. The smoke
reused M5 manager and package caches, created no image, and left this fresh
prefix available for root runtime checks.

The three provisioner invocations were:

```console
AQUA_BINARY=/tmp/score-m5-aqua/host-tools/bootstrap/aqua-2.65.2/aqua \
AQUA_ROOT_DIR=/tmp/score-m5-aqua/aqua-root-host \
UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never \
python3 tools/internal/devcontainer/provision_host_tools.py \
  --profile repository --prefix /tmp/score-m6-aqua/prefix-exposure-fix

# Repeat with --owner-dir /tmp/score-m6-aqua/owners-exposure-fix, whose only
# change was removing buildifier's repository tag; expected retirement: buildifier.
AQUA_BINARY=/tmp/score-m5-aqua/host-tools/bootstrap/aqua-2.65.2/aqua \
AQUA_ROOT_DIR=/tmp/score-m5-aqua/aqua-root-host \
UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never \
python3 tools/internal/devcontainer/provision_host_tools.py \
  --profile repository --prefix /tmp/score-m6-aqua/prefix-exposure-fix \
  --owner-dir /tmp/score-m6-aqua/owners-exposure-fix

# Re-run the first command to restore the current official repository selection.
```

## Generic Node terminal environment

The first real Aqua lifecycle completed post-create provisioning, installed
the repository profile under `/home/node/.local/share/score-tools`, registered
the pre-commit hook, and created the DIND builder. Its later `bash -ic`
terminal check reported `user=node home=/home/node` but failed at `type -P uv`:
the configuration had derived the tools path from `${containerEnv:HOME}`, which
did not match the remote user's home in that lifecycle.

The generic Node configuration now explicitly selects `remoteUser: node` and
sets `SCORE_TOOLS_BIN` and `PATH` to the same
`/home/node/.local/share/score-tools/bin` prefix used by post-create's
`$HOME`-based provisioner. Terminal lookup reaches the direct Aqua/uv and
Python tool entrypoints; no manager wrapper or tool version is added. This
configuration is specific to the selected `javascript-node:4-24` image. The
root reran all three generic Node lifecycle candidates and all passed,
including the actual Aqua terminal lookup for `uv`.

The focused checks below validated the JSONC configuration contract and direct
PATH resolution against the cached uv executable before the real lifecycle
retry. The root-owned lifecycle gate has since passed. Exact focused commands:

```console
python3 - <<'PY'
import json, re
from pathlib import Path
source = Path('.devcontainer/devcontainer.json').read_text(encoding='utf-8')
config = json.loads(re.sub(r'//.*', '', source))
expected = '/home/node/.local/share/score-tools/bin'
assert config['remoteUser'] == 'node'
assert config['remoteEnv']['SCORE_TOOLS_BIN'] == expected
assert config['remoteEnv']['PATH'] == expected + ':${containerEnv:PATH}'
post_create = Path('.devcontainer/post_create_command.sh').read_text(encoding='utf-8')
assert 'SCORE_TOOLS_PREFIX="${HOME}/.local/share/score-tools"' in post_create
print('JSONC parses; remote user, remote PATH, and post-create prefix agree')
PY

mkdir -p /tmp/score-m6-aqua/terminal-home/.local/share/score-tools/bin
ln -sfn /tmp/score-m5-aqua/host-tools/bin/uv /tmp/score-m6-aqua/terminal-home/.local/share/score-tools/bin/uv
ln -sfn /tmp/score-m5-aqua/host-tools/bin/uvx /tmp/score-m6-aqua/terminal-home/.local/share/score-tools/bin/uvx
env HOME=/tmp/score-m6-aqua/terminal-home PATH=/tmp/score-m6-aqua/terminal-home/.local/share/score-tools/bin:/usr/bin:/bin /bin/bash --noprofile --norc -ic 'test "$(type -P uv)" = "$HOME/.local/share/score-tools/bin/uv"; uv --version; test "$(type -P uvx)" = "$HOME/.local/share/score-tools/bin/uvx"; uvx --version'
```

The config assertions passed. The shell check resolved both direct links and
reported uv/uvx `0.13.6`; it used symlinks to the existing M5 cache under
`/tmp/score-m6-aqua`, not copied tool payloads. The later real generic Node
lifecycle also resolved direct prepared tools from the configured user home.

## Real Aqua + uv same-prefix reconciliation

To check the maintained CLI with real managers, I copied
`tools/owners/aqua` to `/tmp/score-m6-aqua/owners-real-reconcile` and started
with a fresh `/tmp/score-m6-aqua/prefix-real-reconcile`. I seeded the prefix
with an unrelated executable named `m6-unrelated-sentinel`. The first real
repository provisioning call used the unmodified owner copy and the existing
M5 manager caches:

```console
AQUA_BINARY=/tmp/score-m5-aqua/bootstrap-test/aqua \
AQUA_ROOT_DIR=/tmp/score-m5-aqua/aqua-root-host \
UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host \
UV_PYTHON_DOWNLOADS=never UV_OFFLINE=1 \
python3 tools/internal/devcontainer/provision_host_tools.py \
  --profile repository \
  --prefix /tmp/score-m6-aqua/prefix-real-reconcile \
  --owner-dir /tmp/score-m6-aqua/owners-real-reconcile
```

Aqua 2.65.2 copied the pinned repository binaries from its M5 root cache;
offline uv 0.13.6 installed `pre-commit==4.7.0` from its M5 wheel cache. The
initial ledger contained actionlint, bazelisk, buildifier, ruff, shellcheck,
uv/uvx, yamlfmt, and pre-commit. Then I replaced the `actionlint` path with a
user script and removed only the `repository` tag from actionlint and buildifier
in the copied `aqua.yaml` (both still have the `published` tag). The resulting
owner-only selection delta was:

```diff
   - name: rhysd/actionlint@v1.7.7
     tags:
       - published
-      - repository
   - name: bazelbuild/bazelisk@v1.27.0
...
   - name: bazel-contrib/buildtools/buildifier@v8.2.1
     tags:
       - published
-      - repository
```

I ran the same maintained provisioner command again with the same prefix and
M5 caches. It exited 0 and reported `"retired_commands": ["buildifier"]`.
The old owned buildifier executable was gone. The changed actionlint path
remained and printed `user-replaced-actionlint`; the unrelated sentinel
remained and printed `m6-unrelated-sentinel`. The final ledger contained only
the retained repository commands: `bazelisk`, `pre-commit`, `ruff`,
`shellcheck`, `uv`, `uvx`, and `yamlfmt`.

I executed the retained commands from that prefix. They reported Bazelisk
`1.27.0` (with cached Bazel `8.6.0` in batch version mode), Ruff `0.11.12`,
ShellCheck `0.10.0`, uv and uvx `0.13.6`, yamlfmt `0.17.0`, and pre-commit
`4.7.0`. Aqua logs showed cached executable copies; uv resolved 11 packages in
2 ms with `UV_OFFLINE=1`. The prefix apparent size was `116326719` bytes, below
150,000,000 bytes. No image or container was run; the existing M5 manager
caches were reused. Aqua and uv materialized only the selected commands in the
M6 prefix; the M5 prepared host-tools tree was not bulk-copied.

This real reprovision covers same-profile native deselection, removal of an
unchanged owned executable, preservation of a user-replaced deselected path,
preservation of an unrelated path, and execution of the retained pinned native
and Python commands. Cross-profile repository/published sharing, Python alias
sharing/retirement, and the additional foreign/symlink replacement cases
remain covered by the fake-manager fixture only; no real published/APM profile
was provisioned for this check.

## One-time and recurring maintenance

For a prefix without the supported ownership ledger, select a fresh prefix once:

```console
python3 tools/internal/devcontainer/provision_host_tools.py \
  --profile repository --prefix /absolute/path/to/new-score-tools
```

Existing unrelated names do not block provisioning. If a selected name already
exists and is not recorded as owned, move that name yourself or choose a fresh
prefix. The provisioner preserves it and stops before replacing it.

After editing an owner or accepting a Renovate update, recurring owner work is:

```console
python3 tools/internal/aqua/refresh_owners.py
python3 tools/internal/aqua/sync_repository.py --check
python3 tools/internal/sync_readme.py --check
```

For a local Python dependency release, provide an explicit version and package
identity each time. Example values below are local candidate inputs, not
selected public release policy:

```console
UV_BINARY=/path/to/uv python3 tools/internal/aqua/prepare_dependency_release.py \
  --output /tmp/score-aqua-release \
  --version 0.4.0 \
  --package-name score-aqua-m6-local
python3 tools/internal/aqua/check_dependency_release.py \
  /tmp/score-aqua-release /tmp/score-aqua-check \
  --uv /path/to/uv --uvx /path/to/uvx
```

The output directory must be fresh. The package requires no SCORE runner and
uses no duplicated tool pins. Release identity/hosting and any eventual
publishing flow remain undecided.

## Focused checks and results

| Check | Exact command or evidence | Result |
| --- | --- | --- |
| Python syntax | `python3 -m py_compile tools/internal/aqua/python_package.py tools/internal/aqua/prepare_dependency_release.py tools/internal/aqua/check_dependency_release.py tools/internal/aqua/sync_repository.py tools/internal/devcontainer/provision_host_tools.py tools/tests/test_provision_host_tools.py tools/tests/test_aqua_python_package.py experiments/tool-manager-aqua/reference/prepare.py experiments/tool-manager-aqua/reference/check.py` | Exit 0. |
| New regression checks | `python3 -m unittest tools.tests.test_provision_host_tools tools.tests.test_aqua_python_package` | 13 tests passed. Includes an Aqua `cp` extra-`gh` regression, foreign `gh` preservation, selected-output validation, and deselection, alongside co-owned profile commands, user-replaced regular/symlink commands, unsupported state, command aliases, owner-derived metadata, and explicit package identity. |
| Ruff and formatting | Exact `ruff check` and `ruff format --check` commands are listed below. | Both passed; all nine files already formatted after cleanup. |
| Compatibility output drift | `python3 tools/internal/aqua/sync_repository.py --check`; `python3 tools/internal/sync_readme.py --check` | Both exit 0; sync reports `"changed": []`. |
| Production experiment-path audit | `rg -n 'experiments/' tools/internal/aqua tools/internal/devcontainer/provision_host_tools.py tools/tests/test_aqua_python_package.py tools/tests/test_provision_host_tools.py` | No matches; production update/export and package checks do not read or write `experiments/`. |
| Cross-profile reconciliation fixture | `python3 /tmp/score-m6-aqua/reconcile_fixture.py` | Passed with Aqua/uv test doubles. Cross-profile repository/published shared native and Python aliases, alias retirement, and additional foreign/symlink replacement cases remain fixture-only; the new real same-profile check is described above. |
| Real Aqua/uv same-prefix repository reprovision | Same `AQUA_BINARY=... AQUA_ROOT_DIR=... UV_CACHE_DIR=... UV_OFFLINE=1 python3 tools/internal/devcontainer/provision_host_tools.py --profile repository --prefix /tmp/score-m6-aqua/prefix-real-reconcile --owner-dir /tmp/score-m6-aqua/owners-real-reconcile` command before and after copied-owner tag changes. | Aqua 2.65.2 copied from the existing M5 cache; uv 0.13.6 ran with `UV_OFFLINE=1` using the existing M5 cache. `buildifier` was retired, replaced `actionlint` and the unrelated sentinel survived, and all retained commands ran at their owner pins. Prefix apparent size was 116,326,719 bytes. |
| Real cached-manager exposure smoke | Maintained provisioner on `/tmp/score-m6-aqua/prefix-exposure-fix` using current owner, then copied owner with only buildifier's repository tag removed, then current owner restored. | Actual Aqua 2.65.2 plus uv 0.13.6; only M5 caches reused. Copy output was privately staged, `gh` was absent, selected commands executed, and real reprovision retired buildifier. Final current-owner prefix was 125 MiB (`du -sh`). |
| Real uv script staging | `UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host UV_TOOL_BIN_DIR=/tmp/score-m6-aqua/uv-stage/exposure UV_TOOL_DIR=/tmp/score-m6-aqua/uv-stage/tools UV_PYTHON_INSTALL_DIR=/tmp/score-m6-aqua/uv-stage/python UV_PYTHON_DOWNLOADS=never /tmp/score-m5-aqua/host-tools/bin/uv --no-config tool install --force pytest==9.0.2` | Exit 0; uv reported `Installed 2 executables: py.test, pytest`, matching the maintained command identity catalog. It used the M5 cache and wrote new output only under `/tmp/score-m6-aqua`. |
| Local dependency wheel | `UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host UV_PYTHON_DOWNLOADS=never UV_BINARY=/tmp/score-m5-aqua/host-tools/bin/uv python3 tools/internal/aqua/prepare_dependency_release.py --output /tmp/score-m6-aqua/release --version 0.4.0 --package-name score-aqua-m6-local` | Exit 0. Built `score_aqua_m6_local-0.4.0-py3-none-any.whl`; SHA-256 `d0449b5c8526945ffc730e41079ab4d4ef9c00e7ccd2d022a1bb318449c73ec0`. Manifest owner digest `5c735127f1e58cda237e8c6d9b046355223e088113701c896abb8d70885c0de3`. |
| Ordinary local-wheel consumer | `UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host UV_PYTHON_DOWNLOADS=never UV_BINARY=/tmp/score-m5-aqua/host-tools/bin/uv UVX_BINARY=/tmp/score-m5-aqua/host-tools/bin/uvx python3 tools/internal/aqua/check_dependency_release.py /tmp/score-m6-aqua/release /tmp/score-m6-aqua/wheel-check-m6` | Exit 0. Direct `uv add`, `uv lock`, `uv sync --locked`, `uv run --locked ruff --version`, and `uvx --with <local wheel> ruff --version` all used the local package and printed Ruff `0.11.12`. Consumer `uv.lock` records the wheel as a local path. |
| Public Bazel and direct strict execution | No M6 runner/Bazel source changed. See [README-m5.md](README-m5.md) for the inherited exact passing commands and results. | Not rerun for M6; the production runner path is unchanged. |

The fake-manager reconciliation fixture remains the only evidence for
cross-profile repository/published sharing and its broader alias/symlink cases.
The bounded real manager check above used actual Aqua and uv for repository
profile deselection. The local-wheel gate also uses real uv and uvx. No full
image or real published/APM profile was run. Owner refresh did not need a
network checksum update because no owner version changed.

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

All three generic Node lifecycle gates passed, and Nix/Mise full builds plus
feature suites passed. Root owns the remaining Aqua published image retry;
the Aqua image worker did not run a full image build. Exact build command:

```console
npm exec --yes --package=@devcontainers/cli -- devcontainer build \
  --workspace-folder src/s-core-devcontainer \
  --image-name score-aqua-m6:linux-amd64 \
  --platform linux/amd64
```

The missing executable bit on `provision_image_tools.sh` is fixed. The Aqua
`gh` collision is fixed at command exposure: the owner-selected native commands
alone enter the direct-tool prefix, and the feature's ordinary PATH check stays
unchanged. Root owns the fresh retry and final aggregate review. No image build,
hosted workflow run, publication, commit, or cross-platform binary execution is
claimed here.
