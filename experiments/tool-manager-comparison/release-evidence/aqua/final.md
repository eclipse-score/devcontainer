<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M8 Aqua local release and same-consumer update

All requested M8 workflow boundaries passed on Linux x86_64 as uid/gid 1000.
Two ordinary wheels of the candidate-local `score-aqua-m8-local` package were
built outside the source tree: A 0.8.0 from current owners, and B 0.8.1 from
an isolated Ruff 0.14.6 owner edit. Worktree owner pins remain unchanged.
No production Python/shell implementation changed. The supported maintainer/user
sequence is now in `tools/internal/aqua/README.md`; `tools/internal/README.md`
links there in place of its shorter release command snippet.

## Actual commands and outcomes

All paths below are local evidence, not production dependencies. `S` contains
only copied maintained tools, module files, and small config required by catalog
validation (about 0.9 MiB); no experimental generator or runtime tree was copied.
`/tmp/score-m8-aqua/commands.sh` and `evidence/commands.json` record 41 exact
commands, cwd, expected exit, and raw-log paths. They are an audit transcript;
reproduction needs fresh release/check output directories and the owner edit at
the indicated boundary, not blindly rerunning the transcript against final B.

```sh
S=/tmp/score-m8-aqua/source
R=/tmp/score-m8-aqua
UV=/tmp/score-m6-aqua/prefix-exposure-fix/bin/uv
UVX=/tmp/score-m6-aqua/prefix-exposure-fix/bin/uvx
export AQUA_BINARY=/tmp/score-m5-aqua/bootstrap-test/aqua
export AQUA_ROOT_DIR=/tmp/score-m5-aqua/aqua-root-host
export UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host
export UV_PYTHON_DOWNLOADS=never
python3 "$S/tools/internal/aqua/prepare_dependency_release.py" \
  --output "$R/handoff/A" --version 0.8.0 \
  --package-name score-aqua-m8-local --uv "$UV"
python3 "$S/tools/internal/aqua/check_dependency_release.py" \
  "$R/handoff/A" "$R/check-A" --owner-dir "$R/owners-A" \
  --uv "$UV" --uvx "$UVX"
python3 "$S/tools/internal/devcontainer/provision_host_tools.py" \
  --profile repository --prefix "$R/native-prefix"
```

All three exited 0 with A owners. Saved the native command fingerprints and
created an unrelated executable sentinel. Then changed exactly this authored
line in the copied owner (full `evidence/authored.diff`):

```diff
-  - name: astral-sh/ruff@0.11.12
+  - name: astral-sh/ruff@0.14.6
```

The target was supplied from prior historical Nix experiment knowledge. This
run does not claim free arbitrary-version discovery and did not use Nix or
experimental source as an Aqua production input. The existing pinned standard
Aqua registry supports the target; no new recipe/layout translation was needed.

```sh
python3 "$S/tools/internal/aqua/sync_repository.py" --check
# Expected exit 1: Missing resolved aqua checksum for Ruff 0.14.6.
python3 "$S/tools/internal/aqua/refresh_owners.py"
python3 "$S/tools/internal/aqua/sync_repository.py" --check
python3 "$S/tools/internal/sync_readme.py" --check
python3 "$S/tools/internal/aqua/prepare_dependency_release.py" \
  --output "$R/handoff/B" --version 0.8.1 \
  --package-name score-aqua-m8-local --uv "$UV"
python3 "$S/tools/internal/aqua/check_dependency_release.py" \
  "$R/handoff/A" "$R/reject-A" --uv "$UV" --uvx "$UVX"
# Expected exit 1: Release owner digest is stale.
python3 "$S/tools/internal/aqua/check_dependency_release.py" \
  "$R/handoff/B" "$R/check-B" --uv "$UV" --uvx "$UVX"
python3 "$S/tools/internal/devcontainer/provision_host_tools.py" \
  --profile repository --prefix "$R/native-prefix"
```

Refresh/check, B build/check, and same-prefix reprovision exited 0. A final
reprovision reported `status: current`. Generated changes are exactly four
Ruff checksum records, the Ruff portable lockfile, and its generated README
row (`evidence/generated.diff`). Neither profile membership nor any unrelated
version changed; the Python owner and Aqua bootstrap inputs remain identical.
The portable Linux x86_64 archive hash is
`7ef1743875c7c469cc1c4bb6da6a9bbff3f3a7b89a75632d6cd2944ede470a5e`.

## Independent ordinary Python consumer

Both wheels were copied to `$R/handoff/wheels`. The same independent directory
`$R/consumer` started with dependency
`score-aqua-m8-local[ruff]==0.8.0`, then changed only that requirement to 0.8.1.
There is no Ruff requirement in its authored `pyproject.toml`.

```sh
cd /tmp/score-m8-aqua/consumer
"$UV" --no-config lock --python /usr/bin/python3 \
  --find-links /tmp/score-m8-aqua/handoff/wheels
"$UV" --no-config sync --locked --offline
"$UV" --no-config run --locked --offline ruff --version
"$UV" --no-config run --locked --offline ruff check --isolated 'bad input.py'
"$UVX" --no-config --offline --find-links /tmp/score-m8-aqua/handoff/wheels \
  --with 'score-aqua-m8-local[ruff]==0.8.0' ruff --version
```

Ran that sequence for A, then B with only the facade version changed (also
in uvx). Versions were Ruff 0.11.12 then 0.14.6. Ordinary uvx additionally ran
the same failing check for both releases. The file contains `import os`;
all four negative checks reported F401 and exit 1, preserving the spaced filename.
Both lockfiles and wheel `Requires-Dist` metadata are retained in `evidence`.
B's wheel declares `ruff==0.14.6; extra == "ruff"`; B's lock records
`ruff 0.14.6` from PyPI and facade 0.8.1 from the local wheel directory.
The uv update explicitly reports only those two package changes.

The producer used Python 3.12.3. The independent project permits Python >=3.12;
uv chose already installed Python 3.14.3 for its venv. No interpreter was
downloaded. Final B uv/uvx calls passed with Aqua environment variables removed
and manager/Bazel interceptors on PATH; no interceptor ran. This consumer needs
Python, uv, the wheel handoff and normal Python package access/cache, not the
producer source, Aqua, or a SCORE wrapper.

## Native prefix and public Bazel boundary

A and B use the same `$R/native-prefix`, owned by uid 1000. Ruff changed from
0.11.12 to 0.14.6. The unrelated user sentinel still executes `user-sentinel`;
actionlint, uv, pre-commit and sentinel fingerprint/realpath records are
unchanged. All nine repository-selected command paths remain, and no unselected
`gh` exists. `evidence/native-A.json` and `native-B.json` retain the fingerprints.

With `SCORE_TOOLS_BIN=$R/native-prefix/bin`, `RUN_TOOL_CONTAINER_MODE=host`,
and Aqua/uv/Bazel/Bazelisk trap executables prepended to PATH:

```sh
"$R/native-prefix/bin/ruff" check --isolated "$R/consumer/bad input.py"
"$S/tools/run-tool" --strict ruff --version
"$S/tools/run-tool" --strict ruff check --isolated "$R/consumer/bad input.py"
```

Direct/strict checks returned the same F401/exit 1; strict version was 0.14.6.
No interception marker exists. Native runtime is direct; actual Aqua and uv
were used during provisioning, not doubles.

The explicit compatibility consumer reused the existing candidate Bazel cache:

```sh
cd /tmp/score-m8-aqua/source
bazel --output_base=/tmp/score-m5-aqua/bazel --host_jvm_args=-Xmx512m run \
  --repository_cache=/home/alex/.cache/bazel/_bazel_alex/cache/repos/v1 \
  --symlink_prefix=/tmp/score-m8-aqua/bazel- //tools:ruff -- --version
cd 'consumer fixture'
bazel --output_base=/tmp/score-m5-aqua/bazel --host_jvm_args=-Xmx512m run \
  --repository_cache=/home/alex/.cache/bazel/_bazel_alex/cache/repos/v1 \
  --symlink_prefix=/tmp/score-m8-aqua/bazel- //tools:ruff -- \
  check --isolated 'bad input.py'
```

The unchanged public label selected generated Ruff 0.14.6 and exited 0 for
version. The subdirectory check resolved the relative spaced filename in the
caller's cwd and propagated F401/exit 1. This tests Bazel compatibility only.

## API findings and source maintenance ledger

| Responsibility | Result / remaining operation |
| --- | --- |
| One-time source repair | None needed in implementation. Added maintained workflow README and replaced the shorter internal release snippet with a link. Inherited changes preserved. |
| Per-version authoring | One native owner line; target availability is given historical knowledge. Refresh obtains all supported checksums and derives compatibility views. No second authored Ruff pin. |
| Per-release operation | Explicit version/name, ordinary uv wheel build, owner/hash-bound validation, retain artifacts/manifests, and Bazel compatibility verification. |
| User operation | Change only facade release requirement and lock/sync, or reprovision the same user prefix using current owners. No ordinary runtime wrapper. |
| Platform work | Existing registry and portable-layout adapters remain necessary. M8 executes amd64 only; ARM/macOS and hosted releases are outside this run. |
| Removed paths | None. Refresh, sync, prepare, check and provision are distinct exercised boundaries; no helper was demonstrated redundant. Historical evidence stays. |

Current API limits: stale native checksum checking emits a traceback rather than
a concise drift message; refresh revisits bootstrap/all package checksum data;
the release checker requires a fresh consumer and tests the repository extra
(the actual same-project update here uses ordinary uv); native reprovision
recopies selected outputs and force-installs Python tools from cache. Wheel
build isolation resolves `setuptools>=77`, so byte-identical rebuilding with a
locked backend is not claimed. Consumer lockfiles own their transitive Python
resolution. No unexpected external failure remained.

Initial staging omitted config files needed by the catalog reader (Renovate,
ordinary/proxy Dockerfiles); copying only those small maintained configs fixed
the harness before release acceptance. These were not candidate API failures.
No implementation tests were added or rerun for documentation-only source work.
Current-worktree and copied-B sync/README checks, whitespace checks, JSON/TOML
assertions, unchanged-owner comparisons, command expected-exit assertions,
source hashes, and shebang/mode audits passed. Production references to
`experiments/` remain absent.

`/tmp/score-m8-aqua/result.json` contains manifests and artifact hashes;
`evidence/source-hashes.json` fingerprints the exercised maintained sources.
Raw logs stay under `/tmp/score-m8-aqua/logs`. Task files consumed about 194 MiB;
shared free disk remained above 4 GiB (9.2 GiB at the final check). Existing
manager/Bazel caches were reused; no images/containers/full payload copies,
global installs, commits, or publication occurred. Network was available for
preparation/locking; explicit offline uv sync/run/uvx passed, but this was not a
network-isolated host. No hosting or public package identity is selected.

## Artifact bindings

| Release | Owner digest | Wheel SHA-256 |
| --- | --- | --- |
| A 0.8.0 | `5c735127f1e58cda237e8c6d9b046355223e088113701c896abb8d70885c0de3` | `5fb94ac928e3253dc3d76fd537f5c341fb3b941ac50a09478850deced57543f1` |
| B 0.8.1 | `7d95dfc5f2caf3898b44fbcd13443b2e5da726fbb16b0fe966f40584c9e20023` | `dc3203a6557b0db411bb6aab5204b9993f898d4a4a929a073ca8437c560f7012` |
