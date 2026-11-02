<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M8 mise handoff

Stable candidate source and complete local A → B workflow evidence are ready
for root comparison. The candidate's accepted owner and compatibility pins
remain unchanged. All version changes used small current-source copies under
`/tmp/score-m8-mise/sources/{a,b}`. No other worktree, root comparison,
publication, commit, push, nested agent/CLI, global installation, full image,
ARM/macOS execution, or adoption decision was involved.

The maintained guide is
`tools/internal/mise/README.md`; durable candidate evidence is
`experiments/tool-manager-mise/reference/README-m8.md`. Machine-readable
commands, source/artifact/log hashes, results, and constraints are in
`/tmp/score-m8-mise/result.json`. Raw logs and compact diffs/lock snapshots are
under `logs/` and `evidence/`; checked local releases are under `handoff/`.

## Source repair and checks

`refresh.py` used an assertion for owner/artifact-lock version equality. It
gave an opaque error and could be bypassed with Python optimization. It now
raises an explicit stale-lock error naming the backend, owner/lock versions,
and normal refresh command. A targeted regression runs normal and optimized
Python. Four tests in the affected module passed, and the corresponding
`//tools:mise_python_package_test` target passed in the B source copy. Ruff
lint/format, current/copied refresh and inventory checks, release checks, and
`git diff --check` passed. Standalone CLI modes remain 755.

The first actual owner edit was rejected before refresh. The repaired
optimized check was also rejected. Normal `refresh.sh` resolved Ruff 0.14.6
and regenerated current artifacts. A separate stale-generated-Bazel-JSON test
was rejected and repaired through that same normal refresh. The only version
authorship was `aqua:astral-sh/ruff` 0.11.13 → 0.14.6. That target came from
prior historical knowledge supplied by the task, then used ordinary mise
backend resolution; there was no arbitrary version discovery or production
dependency on an experiment generator.

Exactly four files differ between A and B: the native owner TOML, native mise
lock, Ruff portable Bazel lock, and generated README Ruff row. All other pins,
locked native records and environment selections remain unchanged.

## Release and user results

| Delivery | A | B |
| --- | --- | --- |
| Local facade | `score-mise-m8-local` 0.8.0 | Same name, 0.8.1 |
| Ruff Requires-Dist | `ruff==0.11.13; extra == "ruff"` | `ruff==0.14.6; extra == "ruff"` |
| Wheel SHA-256 | `8f1329084e0558a4817fba6857f1fa06e17efda6d7284840cc74a4b0c787a491` | `bfbffe7f199610a6f71f07c18733a8ea9cff7e23b41cca3f4a817a5462e7e4e1` |
| Same uv consumer | Ruff 0.11.13 | Ruff 0.14.6 |
| Ordinary uvx | Ruff 0.11.13 | Ruff 0.14.6 |
| Same native prefix | Ruff 0.11.13 | Ruff 0.14.6 |

Both releases passed their current-owner check. Validating A using B's source
was rejected with `Local release is stale for extras`. Release manifests bind
identity, owner hashes, extras, and wheel hashes. Neither identity nor hosting
has been selected for public use.

The same independent uv project changed only its facade requirement from
0.8.0 to 0.8.1, then locked/synced the existing environment. Neither project
state contained a manually copied Ruff pin. Both uv and uvx paths returned the
expected F821/exit 1 for `bad input.py`. The final B repeat passed with
`UV_OFFLINE=1` and poisoned manager/Bazel PATH; this was a host process with
uv offline flags, not OS network namespace isolation. It used no producer
manager or source code. Consumer prerequisites are compatible uv/Python, the
handoff wheel directory, and dependency index/network or cached metadata and
wheels.

Native A and B reprovisioned the same user-owned
`/tmp/score-m8-mise/native/bin` with the `repository` selection and reused
`/tmp/score-m5-mise/provision-data`. B installed only new Ruff; eight other
selected command targets/hashes and the unrelated user script stayed equal.
Five direct/strict cases passed for each release with no manager/Bazel marker.

From B's source copy the existing public `//tools:ruff` target returned
Ruff 0.14.6, then the expected F821/exit 1 for the spaced filename in the
caller directory. Its generated artifact URL/checksum/member matched the
mise lock. The Bazel binary matched native B's SHA-256
`2c8c2a0b5963e1d530ce16852ac477bfd1f4f2075497d7d30728fccb562ec330`.
This was an explicit compatibility test; ordinary uv/native calls did not
depend on Bazel.

## Exact API sequence

```sh
# B, after the one-line owner edit (A uses the corresponding a source path):
MISE_BINARY=/tmp/score-m3-mise/bootstrap/mise /tmp/score-m8-mise/sources/b/tools/internal/mise/refresh.sh
python3 /tmp/score-m8-mise/sources/b/tools/internal/mise/refresh.py --check
python3 /tmp/score-m8-mise/sources/b/tools/internal/mise/python_package.py build --output /tmp/score-m8-mise/handoff/b --version 0.8.1 --package-name score-mise-m8-local --uv /tmp/score-m5-mise/provision-bin/uv
python3 /tmp/score-m8-mise/sources/b/tools/internal/mise/python_package.py check /tmp/score-m8-mise/handoff/b
python3 /tmp/score-m8-mise/sources/b/tools/internal/mise/provision.py repository --data-dir /tmp/score-m5-mise/provision-data --bin-dir /tmp/score-m8-mise/native/bin --mise /tmp/score-m3-mise/bootstrap/mise

# In the same independent consumer after changing only the facade requirement:
/tmp/score-m5-mise/provision-bin/uv lock --find-links /tmp/score-m8-mise/handoff/wheels
/tmp/score-m5-mise/provision-bin/uv sync --locked --find-links /tmp/score-m8-mise/handoff/wheels
/tmp/score-m5-mise/provision-bin/uv run --no-sync ruff --version
/tmp/score-m5-mise/provision-bin/uvx --find-links /tmp/score-m8-mise/handoff/wheels --from 'score-mise-m8-local[ruff]==0.8.1' ruff --version

# In sources/b, explicit Bazel compatibility:
/tmp/score-m5-mise/host-bin/bazelisk --batch --output_base=/tmp/score-m8-mise/bazel run --repository_cache=/home/alex/.cache/bazel/_bazel_alex/cache/repos/v1 //tools:ruff -- --version
/tmp/score-m5-mise/host-bin/bazelisk --batch --output_base=/tmp/score-m8-mise/bazel run --repository_cache=/home/alex/.cache/bazel/_bazel_alex/cache/repos/v1 //tools:ruff -- check --output-format concise 'bad input.py'
```

Build output paths above already exist: reproduction builds must use fresh
empty destinations. The guide describes normal supported user paths; the
task-only probes record exact direct/strict argv, cwd and exits.

## Removal decision and responsibilities

Removed instructions: Git-selected `score-tool` consumer examples and duplicate
fixed-version wheel build snippets in `tools/README.md` and
`tools/internal/README.md`. The maintained guide consolidates the full sequence.
No helper file was deleted: each bootstrap/refresh/package/provision helper
still has a demonstrated role. Existing root packaging, `score-tool`, Bazel
targets and run-tool fallback remain compatibility surfaces. No historical
report was deleted.

| Cadence | Work |
| --- | --- |
| One-time | Explicit optimization-safe stale validation, targeted regression, supported guide and obsolete-instruction cleanup. |
| Per version | Single owner edit, normal lock/export/inventory refresh, diff review, affected tool execution. |
| Per release | Explicit name/version, build/check, owner binding, artifact digest and local handoff. |
| Per platform | Verify backend/bootstrap coverage, artifact hashes/layouts, and execute on the target platform. No platform recipe changed in M8. |
| Per user update | Facade requirement + uv lock/sync, or native environment reprovision into the existing prefix. |

Execution was Linux x86_64 as uid 1000, Python 3.12.3, using M5/M6 amd64
caches. No M7 payload was required. Disk remained above 4 GiB free; the final
task tree was about 319 MiB including Bazel, plus about 34 MiB new native Ruff
in the existing manager data tree and small incremental package caches.
Full raw source/runtime directories are not needed in root's compact archive.
No persistent external failure remains in the requested M8 scope; ARM/macOS,
public hosting/identity and the complete migration remain outside this run.
