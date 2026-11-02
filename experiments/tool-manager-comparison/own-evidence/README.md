<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Own provisioning: compact local evidence

Source checkout: `score_devcontainer-eval-own`, branch `eval/tool-manager-own`,
base `2e337e41fba86ea7a94ee3d5e58cf3c4f7d93561`. No commit or publication.
See [implementation and comparison](../../../docs/tooling-own-provisioning.md).

## Results

| Executed boundary | Result |
| --- | --- |
| Focused unit regressions | 45 passed, including inherited tests, safe file/link conflicts, shared archive siblings, bounded retries, owner/wheel binding and generated removal. |
| Existing public Bazel shell tests | Both passed; original cwd/argv/nonzero and container/host fallback contracts retained. |
| Actual existing Python Bazel target | `//tools:pre-commit -- --version` ran pre-commit 4.7.0. |
| Ordinary release/update workflow | A 0.8.0 / Ruff 0.11.13 -> B 0.8.1 / Ruff 0.14.6 passed through maintained build/check, same uv project, ordinary uvx, same native prefix and public Bazel target. |
| Generic Node lifecycle | Passed on final source: real `up`, post-create, node terminal, hook, DinD and Buildx. Task-only terminal retry policy allows at most three attempts in the same container; assertions are unchanged. |
| Full current feature suite on cached Ubuntu providers | 81 checks passed as vscode, using newly prepared selected native/Python tools and current source tests. This is not a fresh provider/image build. |
| Prepared direct/strict and behavior checks | 16 direct/strict comparisons plus two behavior checks passed offline/read-only as uid 1000; no intercepted resolver/manager/Bazel launch. |
| IDE protocols / launcher | Ruff, Starpls and basedpyright language servers initialize/shutdown successfully. Guarded actual Bazelisk runs without downloading an engine. |
| Fresh full amd64 image + feature gate | **Passed**, original production URLs, no artifact override: 79 unchanged-suite assertions as vscode inside the fresh no-cache build. Cache-only output; task builder removed. Earlier disk cancellation remains a failure record. |
| ARM64 prepared tools | **Passed under QEMU**, original URLs: newly prepared current selection, uid 1000, offline/read-only, same direct/strict/behavior/IDE checks. All 16 exposed paths point into the new prefix; native commands, interpreter and bundled Node are AArch64 ELF. |
| Fresh full ARM64 image + feature gate | **Not passed.** First attempt hit its 30-minute cap during pycairo build-dependency installation after 16 assertions. A 45-minute retry failed at preserved Bazel-engine acquisition with a peer connection reset, before the suite and without hitting its cap. Both used production URLs; task builders removed. |
| Targeted ARM64 provider recovery | Newly prepared Bazelisk downloaded and ran real Bazel 8.6.0 in isolated uid-1000 cache, then ran it offline. Diagnoses a transient acquisition failure; not an image/suite pass. |
| Native ARM hardware / macOS | Not executed; QEMU does not establish hardware or macOS support. |

`results.json` records commands and boundaries. `source-manifest.json` and
`sources/` identify maintained final source. `peer-sources.json` fingerprints
the read-only references actually consulted; peer runtime claims are not own
results. The final Node gate and cached feature suite include their source
hashes. The original disk-blocked full-build attempt uses its earlier source
snapshot; the successful fresh amd64 retry binds current implementation, owners,
image configuration and unchanged test sources. Per-run adapter/harness bindings
distinguish the new gates from historical failures.

## Reproducible maintained entrypoints

```sh
python3 -m unittest discover -s tools/tests -p 'test_*.py'
python3 tools/internal/sync_readme.py --check
bazel test //tools:run_tool_test //tools:python_tool_runner_test
python3 tools/tests/release_smoke.py --output /tmp/own-release-FRESH
python3 tools/tests/prepared_smoke.py --prefix PREPARED_PREFIX --output FRESH_DIR/prepared.json
```

The last check needs the prepared full native/Python selection, compatible
interpreter/provider support, and a writable output directory. Network denial,
uid and read-only mounts are runtime conditions supplied by the caller, not
silently inferred by the script. `results.json` records the Docker invocation
used here. LSP checks use normal provider PATH; Starpls's workspace `bazel info`
query is functionality, distinct from launch-time Bazel resolution.

## Archived material

- `release/`: command records, two bound manifests, wheel METADATA text,
  generated project metadata, before/after consumer TOML/uv locks, Ruff owner
  snapshots, refresh result, native target/hash/sentinel records and continuity.
  No wheel, executable, checkout or virtual environment payload.
- `integration/`: every Node/full-build result, source hashes when captured,
  terminal retry records and concise failure classification. The cached-substrate
  feature summary, selected observations and exact runtime mirror record are
  separate from fresh image results. New build summaries include assertion names,
  counts and selected tool observations. Fresh gates produce cache-only output,
  not loaded/published runtime images.
- `arm64/`: exact preparation/offline/inspection commands, source hashes, direct
  and strict outputs, LSP responses and independent ELF/path inspection. The
  retained final-arm64 image supplies OS providers, not the tested tool output.
- `prepared.json`: exact direct/strict arguments, cwd, exit/stdout/stderr, real
  behavior, protocol response IDs and guarded Bazelisk output.
- `sources/`: small maintained implementation snapshots, not another runtime or
  production caller. `provenance.json` hashes the archive.

Acquisition was online. The non-root prepared checks used `--network none`
and read-only root/prefix. Container urllib timed out three times downloading
OpenCode; bounded host curl fetched the **same upstream archive**, verified
against the original SHA256, then a task-only catalog changed that one URL to
`file://`. No production owner/version/hash changed. This mirror proves the
existing installer transport boundary, not a new persistent artifact-cache
feature or successful original-URL acquisition in that earlier container.
The later fresh amd64 gate and ARM64 preparation used the production URLs
successfully, with no mirror or production owner changes.

Historical failures remain classified: a real uvx adjacency bug was fixed;
later registry resets/timeouts and reserve-triggered cancellations are not
counted as passes. A host-created Python environment initially depended on
host uv-managed Python 3.14 and could not run in the Ubuntu substrate; production
preparation now defaults to its provisioning interpreter, with explicit
`UV_PYTHON` override retained. The final prepared environments use Ubuntu Python
3.12. A pipelined LSP fixture was corrected to await protocol responses.

The original main and sibling source files were only read. Initial in-place
harness imports did not disable Python bytecode writes, so an incidental ignored
cache write cannot be ruled out; no potentially shared cache was deleted. The
archived adapter now disables bytecode writes without changing gate assertions.
Outputs otherwise stay in this worktree and task-owned `/tmp`/Docker resources.
Shared caches/base images were reused without deleting other workers' resources.
Automatic cleanup of developer installations is outside the corrected scope.
The parent-authorized obsolete-image cleanup is separately recorded; absence of
those older runtime tags is not loss of archived source/evidence.
