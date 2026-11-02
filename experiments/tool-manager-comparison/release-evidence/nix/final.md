<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Nix M8 handoff

Completed the six requested local release/update boundaries in the Nix candidate.
Current worktree pins remain unchanged. Isolated B uses the known historical
Nixpkgs revision `b6018f87da91d19d0ab4cf979885689b469cdd41` for Ruff alone.

| Release | Ordinary local wheel | Selected Ruff | Native store objects |
| --- | --- | --- | --- |
| A | score-devcontainer-nix-candidate 0.8.0 | 0.17.2 | 183 |
| B | score-devcontainer-nix-candidate 0.8.1 | 0.14.6 | 191 |

Artifacts: `/tmp/score-m8-nix/release-a`, `/tmp/score-m8-nix/release-b` and
`/tmp/score-m8-nix/handoff/*.whl`. Wheel SHA-256:

- A: `301ea5c2fe6ccd982aa88525c17613e44402f5018332cffca0016f68f2d79615`
- B: `efe7e3d95573dce1e6dd4557a2bd366a6d537c56d71615ccc0899a3442b48499`

The owner edit caused `sync.py --check` exit 1; normal sync plus overview refresh
returned clean. A against B owner validation failed as required. Both final
release checks passed, and both bundles plus every exported store path matched
current owner evaluation. All other 14 versions/profile membership remained.
`authored-owner.diff` and `generated.diff` separate authored/derived changes.

The same independent uv project changed only facade requirement 0.8.0→0.8.1.
Ordinary uv add/lock/sync/run and uvx selected each wheel's exact Ruff extra.
Both paths reported each selected version and F401/exit 1. Consumer Python
3.12.3 and uv/uvx 0.13.6 need no Nix, producer, Bazel or SCORE wrapper.
`uv-{a,b}.lock`, `consumer-{a,b}.toml` and wheel METADATA prove the dependency.

The same UID65534-owned native profile upgraded A→B using maintained
`tools/nix/install-host.sh`. The unrelated fixed-store user command and selected
buildifier path/version stayed intact. Direct and host strict calls used new
Ruff and preserved F401/exit 1 with a spaced filename; poison nix/bazel/ruff
commands were never intercepted. Provisioning used the existing producer's Nix
daemon. The installer upgrades all entries; this preservation evidence applies
to the fixed store entry tested, not every independent foreign flake update.

Cached Bazel 8.6.0 executed public `//tools:ruff`: 0.14.6, plus F401/exit 1 from
caller `source-b/tools` cwd using relative `bad input.py`. The generated simple
portable archive selection is captured. This was explicit Bazel compatibility.

Maintained changes: opt-in `prepare.py --reuse-native-from` hardlinks immutable
store files and transfers only missing objects, with independent metadata;
two new regression tests; supported release/user docs; removed obsolete
`tools/internal/nix/Dockerfile` and its export. That file referenced a comparison
image and missing installer. Final fresh prepares without it preserved exact
release/package/activation bytes. Optional package-only generation, pre-commit
smoke helper, membership regression and historical reports remain useful.

Exact principal commands (each harness records every nested argv/cwd/result):

```sh
python3 /tmp/score-m8-nix/stage.py
python3 /tmp/score-m8-nix/edit-owner.py
python3 /tmp/score-m8-nix/source-b/tools/internal/nix/sync.py --check # expected1
python3 /tmp/score-m8-nix/source-b/tools/internal/nix/sync.py
python3 /tmp/score-m8-nix/source-b/tools/internal/sync_readme.py
python3 /tmp/score-m8-nix/source-b/tools/internal/nix/sync.py --check
python3 /tmp/score-m8-nix/source-b/tools/internal/sync_readme.py --check
# Final prepares after cleanup (initial releases renamed *-before-cleanup):
python3 /tmp/score-m8-nix/source-a/tools/internal/nix/prepare.py /tmp/score-m8-nix/release-a --release-version 0.8.0 --package-name score-devcontainer-nix-candidate --reuse-native-from /tmp/score-m8-nix/release-a-before-cleanup
python3 /tmp/score-m8-nix/source-b/tools/internal/nix/prepare.py /tmp/score-m8-nix/release-b --release-version 0.8.1 --package-name score-devcontainer-nix-candidate --reuse-native-from /tmp/score-m8-nix/release-b-before-cleanup
python3 /tmp/score-m8-nix/consumer-check.py
python3 /tmp/score-m8-nix/native-check.py
python3 /tmp/score-m8-nix/bazel-check.py
python3 /tmp/score-m8-nix/release-check.py
python3 /tmp/score-m8-nix/closure-check.py
python3 tools/internal/nix/sync.py --check --release /tmp/score-m8-nix/release-a --system x86_64-linux
python3 tools/internal/sync_readme.py --check
python3 -m unittest discover -s tools/internal/nix -p test_prepare.py
```

These are recorded commands, not an idempotent replay script: some harnesses
create fresh outputs and assert the A state before updating B. Locking commands
and exact smoke argv are in README-m8 and command JSON. Nine focused tests,
source Ruff lint, compile and diff checks passed. No unrelated old suites ran.

Responsibility ledger: one-time repair/cleanup/docs above; per version choose
and verify a package snapshot, lock and refresh compatibility metadata; per
release choose explicit identity, realize/probe, prepare/check and build wheels;
per platform verify substitutes/custom assets/wheels and execute fresh output;
Python user changes facade release and locks/syncs; native user updates owner
checkout and reprovisions the same dedicated profile. Historical snapshot
selection and portable release URL/digest recipes remain manual obligations.

Resource/network limits: initial A reused183/transferred0, B reused180/
transferred11; final prepares reused all. Additional host bytes after accounting
for M6 shared inodes: 455,647,232. Producer adds a 446MiB historical snapshot and
nine substitutes (22.9MiB download /83.6MiB unpacked). Free space stayed above
4GiB, about9GiB at final checks. Acquisition was online; prepared runtime checks
used poison interception, not a separate network namespace. Native amd64 only;
no new images, ARM/macOS execution, nested agents/CLIs, commits/push/publication,
identity/hosting decision or winner claim. No unresolved M8 external failure.

Maintained docs: `tools/internal/nix/README.md`.
Durable report: `experiments/tool-manager-nix/reference/README-m8.md`.
Compact source/artifact/evidence hashes and results: `/tmp/score-m8-nix/result.json`.
Exact logs: `/tmp/score-m8-nix/{consumer,native,bazel}-commands.json` and adjacent
small logs/diffs. All individual compact evidence files are below50KiB.
