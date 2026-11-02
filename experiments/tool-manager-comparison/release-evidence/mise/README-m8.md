<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Mise M8: complete local owner, release, and user update

**2026-11-02:** the maintained workflow completed release A → B through an
independent uv project, ordinary uvx, the same user-owned native prefix, and
the existing public Bazel Ruff target. Actual candidate owner pins remain
unchanged. Version changes ran in small copies of current maintained sources;
no historical generator or runtime tree was copied. No public identity,
hosting, publication, manager adoption, or winner is selected.

The final supported instructions are maintained in
[tools/internal/mise/README.md](/home/alex/git/etas-contrib/score_devcontainer-eval-mise/tools/internal/mise/README.md).
The tools overview and internal maintenance guide link to that sequence.

## Inputs, authored change, and generated output

Task root: `/tmp/score-m8-mise`. Source snapshots are `sources/a` and
`sources/b`, each initially 59 needed maintained files, 402,598 bytes. They
contain tools, root Python/Bazel metadata, and small referenced feature/config
files; no experiments, old release trees, or whole worktree payload.

| Release | Local facade identity | Ruff owner | Wheel SHA-256 |
| --- | --- | --- | --- |
| A | `score-mise-m8-local` 0.8.0 | 0.11.13 | `8f1329084e0558a4817fba6857f1fa06e17efda6d7284840cc74a4b0c787a491` |
| B | `score-mise-m8-local` 0.8.1 | 0.14.6 | `bfbffe7f199610a6f71f07c18733a8ea9cff7e23b41cca3f4a817a5462e7e4e1` |

Only one version was authored in B:

```diff
-"aqua:astral-sh/ruff" = "0.11.13"
+"aqua:astral-sh/ruff" = "0.14.6"
```

Ruff 0.14.6 was a task-selected version already known from historical
experiments; this run did not discover it by a free arbitrary-version search.
Mise resolved its normal backend metadata. No Nix input or experiment source
was read by the maintained APIs. No second Ruff owner pin was edited.

Normal refresh changed exactly four A/B files: `mise.native.toml`,
`mise.native.lock`, `tools/lockfiles/ruff.lock.json`, and the generated Ruff
row in `tools/README.md`. All other native lock records, selections, PyPI pins,
and compatibility definitions were unchanged. The full authored and generated
diffs are `/tmp/score-m8-mise/evidence/{authored-owner,generated}.diff`.

## Stale validation and one-time repair

The first post-edit `refresh.py --check` failed with an unhelpful assertion.
That assertion also vanished under optimized Python, allowing an owner/lock
version mismatch to reach export. The maintained exporter now raises an
explicit stale-lock error with the backend, owner/lock versions, and refresh
command. The regression test exercises both normal Python and `python -O`.
The targeted source diff is `evidence/one-time-repair.diff`; its reconstructed
before state was checked against the recorded starting source hashes.

These actual commands established rejection, normal refresh, and clean output:

```sh
python3 -O /tmp/score-m8-mise/sources/b/tools/internal/mise/refresh.py --check
# exit 1: owner=0.14.6, lock=0.11.13; run tools/internal/mise/refresh.sh
MISE_BINARY=/tmp/score-m3-mise/bootstrap/mise \
  /tmp/score-m8-mise/sources/b/tools/internal/mise/refresh.sh
python3 /tmp/score-m8-mise/sources/b/tools/internal/mise/refresh.py --check
python3 /tmp/score-m8-mise/sources/b/tools/internal/sync_readme.py --check
```

A separate generated-drift check put A's Ruff Bazel JSON into the B copy while
retaining B's current owner and mise lock. `--check` exited 1 with
`Generated drift: tools/lockfiles/ruff.lock.json`. The same normal refresh
command restored byte-identical B output. All final checks passed.

## Ordinary local releases and the same independent consumer

Both artifacts were built outside the source tree and checked against their
own snapshots, using the same candidate-local package name:

```sh
export UV_CACHE_DIR=/tmp/score-m5-mise/uvx-cache
export UV_PYTHON=/usr/bin/python3 UV_PYTHON_PREFERENCE=only-system
python3 /tmp/score-m8-mise/sources/a/tools/internal/mise/python_package.py build --output /tmp/score-m8-mise/handoff/a --version 0.8.0 --package-name score-mise-m8-local --uv /tmp/score-m5-mise/provision-bin/uv
python3 /tmp/score-m8-mise/sources/b/tools/internal/mise/python_package.py build --output /tmp/score-m8-mise/handoff/b --version 0.8.1 --package-name score-mise-m8-local --uv /tmp/score-m5-mise/provision-bin/uv
python3 /tmp/score-m8-mise/sources/a/tools/internal/mise/python_package.py check /tmp/score-m8-mise/handoff/a
python3 /tmp/score-m8-mise/sources/b/tools/internal/mise/python_package.py check /tmp/score-m8-mise/handoff/b
python3 /tmp/score-m8-mise/sources/b/tools/internal/mise/python_package.py check /tmp/score-m8-mise/handoff/a
# last command: expected exit 1, Local release is stale for extras
```

The manifests bind owner hashes, explicit identity/version, extras, and wheel
bytes. Wheel METADATA contains `ruff==0.11.13` for A and `ruff==0.14.6` for B
under the `ruff` extra; all other extras remain unchanged. Full metadata is
retained in `evidence/{a,b}-wheel-METADATA.txt`.

The same project and virtual environment at `consumer/` first selected
`score-mise-m8-local[ruff]==0.8.0`, then changed only `0.8.0` to `0.8.1`.
It never declared a Ruff pin. In that project the ordinary commands were:

```sh
uv=/tmp/score-m5-mise/provision-bin/uv
uvx=/tmp/score-m5-mise/provision-bin/uvx
"${uv}" lock --find-links /tmp/score-m8-mise/handoff/wheels
"${uv}" sync --locked --find-links /tmp/score-m8-mise/handoff/wheels
"${uv}" run --no-sync ruff --version
"${uv}" run --no-sync ruff check --output-format concise 'bad input.py'
"${uvx}" --find-links /tmp/score-m8-mise/handoff/wheels --from 'score-mise-m8-local[ruff]==0.8.0' ruff --version
"${uvx}" --find-links /tmp/score-m8-mise/handoff/wheels --from 'score-mise-m8-local[ruff]==0.8.1' ruff --version
```

The A lock/sync/run selected facade 0.8.0 and Ruff 0.11.13. The B update
changed exactly those two resolved distributions to 0.8.1 and 0.14.6. Both
uvx releases returned the matching version. Both uv-run and uvx paths produced
the deliberate F821 undefined-name diagnostic and exit 1 for `bad input.py`.
`evidence/uv-{a,b}.lock`, `consumer-{a,b}.toml`, and the consumer/uvx failure
files preserve those results. The local flat wheel directory is represented
as a path in uv.lock; the separate checked release manifests bind wheel hashes.

A final B lock/sync/run/uvx repeat passed offline with manager/Bazel poison
executables on PATH and no interception marker. The consumer used only normal
wheel metadata, compatible uv, Python 3.12.3 and its dependency cache. It did
not invoke producer APIs or load producer source. uvx emitted its advisory
that Ruff is supplied by the selected dependency extra, then executed it.

## Same native prefix A → B

Both maintained provisioner calls used the same user-owned
`/tmp/score-m8-mise/native/bin` and existing amd64 mise data/cache:

```sh
python3 /tmp/score-m8-mise/sources/a/tools/internal/mise/provision.py repository --data-dir /tmp/score-m5-mise/provision-data --bin-dir /tmp/score-m8-mise/native/bin --mise /tmp/score-m3-mise/bootstrap/mise
python3 /tmp/score-m8-mise/probes/native-check.py a 0.11.13
python3 /tmp/score-m8-mise/sources/b/tools/internal/mise/provision.py repository --data-dir /tmp/score-m5-mise/provision-data --bin-dir /tmp/score-m8-mise/native/bin --mise /tmp/score-m3-mise/bootstrap/mise
python3 /tmp/score-m8-mise/probes/native-check.py b 0.14.6
```

The repository selection has nine command identities. B installed only the
new native Ruff version; all unchanged selected installations were reused.
Membership stayed equal, eight other selected target paths/hashes stayed
equal, and the unrelated user-owned `user-note` script stayed byte-identical.
Only Ruff's target changed. Each snapshot passed the same five direct/strict
cases: uv, uvx, Ruff and pre-commit versions, plus Ruff's F821/exit 1 with a
spaced filename. Poison mise/Bazel/Bazelisk markers remained absent. Exact argv,
cwd, stdout/stderr and exits are in `evidence/native-{a,b}-calls.json`.
The probe is task verification; the maintained user path is direct `ruff`.

## Public Bazel compatibility

From `sources/b`, these existing public commands passed with the reused
repository cache and a bounded task output base:

```sh
/tmp/score-m5-mise/host-bin/bazelisk --batch --output_base=/tmp/score-m8-mise/bazel run --repository_cache=/home/alex/.cache/bazel/_bazel_alex/cache/repos/v1 //tools:ruff -- --version
/tmp/score-m5-mise/host-bin/bazelisk --batch --output_base=/tmp/score-m8-mise/bazel run --repository_cache=/home/alex/.cache/bazel/_bazel_alex/cache/repos/v1 //tools:ruff -- check --output-format concise 'bad input.py'
```

The target returned `ruff 0.14.6`, then the expected F821/exit 1 from the
caller's B directory. The generated Linux x86_64 artifact URL/hash/archive
member matched the corresponding mise lock exactly. The Bazel-selected binary
SHA-256, `2c8c2a0b5963e1d530ce16852ac477bfd1f4f2075497d7d30728fccb562ec330`,
also matched native B's executable. Bazel was an explicit compatibility test;
ordinary native and Python execution did not require it.

## Maintained documentation and retained helpers

The maintained guide now documents the exact owner edit/refresh, explicit
wheel identity/build/check/handoff, independent uv/uvx update, native
reprovisioning, prerequisites, and compatibility commands. The old Git-selected
`score-tool` release instructions and duplicated fixed-version wheel build
snippets were removed from `tools/README.md` and `tools/internal/README.md`.
The guide is the single full supported sequence; `evidence/maintained-docs.diff`
records the edits.

No helper file was deleted. Bootstrap, lock/export refresh, package build/check,
and prefix reconciliation all still perform demonstrated distinct steps. The
root package and `score-tool` entrypoint remain public compatibility surfaces;
ordinary dependency-wheel consumers no longer need those instructions.
Historical reports and the existing public Bazel/run-tool contracts remain.

| Cadence | Responsibility |
| --- | --- |
| One-time repair | Replace optimization-sensitive stale validation; test normal/optimized Python; consolidate supported docs and remove superseded instructions. |
| Per version | Author one owner edit, resolve platform locks, export compatibility/inventory, review unrelated pins, execute the updated tool. |
| Per release | Choose explicit package name/version, build/check ordinary wheel, retain owner binding/hashes, provide local artifacts. |
| Per platform | Maintain bootstrap/backend/platform URLs, hashes and layouts; execute on that platform. M8 added no recipe/platform data. |
| Per user update | Change only facade release and lock/sync in the same uv project, or reprovision the same native selection/prefix. |

## Checks, constraints, and handoff

The repaired package/export test module passed four unit tests. The affected
`//tools:mise_python_package_test` Bazel target passed. Ruff check/format,
current worktree refresh/inventory checks, copied-source checks, and
`git diff --check` passed. No full image, ARM/macOS or hosted job ran in M8.
Execution was Linux x86_64 as uid 1000; network was used for normal metadata
and package/artifact preparation, with a final cache-backed offline consumer
check. Copies do not prove newly supported platform execution.

Initial free disk after root cleanup was about 11 GiB; later checks remained
above 4 GiB. The task directory was about 319 MiB including the bounded Bazel
output base; new native Ruff was about 34 MiB in the reused manager data tree.
Unchanged runtimes and accepted release metadata were not duplicated or edited.
No M7 payload was required. M5/M6 caches were reused; no global cleanup or
installation occurred.

`/tmp/score-m8-mise/result.json` contains source/artifact/log hashes and exact
commands; `final.md` is the root handoff. Compact evidence is in `evidence/`,
raw logs in `logs/`, local release artifacts in `handoff/`. Root owns the
shared comparison and archive. Existing dirty work and accepted owner pins
were preserved; no commits, pushes or publication were performed.
