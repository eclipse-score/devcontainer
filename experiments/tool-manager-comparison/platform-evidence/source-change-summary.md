<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M7 source-change summary

This summary compares the M7 start inventory with the candidate worktrees after
all three worker turns completed. The captured inventory is archived as
[`source-before.json`](source-before.json); it is a compact source-hash record,
not a source checkout or a cost metric.

- **Mise:** all 82 files in the captured maintained-source inventory retained
their start hashes. The worker reports no M7 maintained-source or pin change;
its candidate `README-m7.md` is evidence documentation.
- **Aqua:** all 88 captured maintained-source files retained their start hashes.
No M7 source repair or pin change was reported. M7 exercised the existing
selected-output promotion against Aqua's real `uv`-related transitive `gh`
copy; `gh` stayed outside the fresh selected command prefix.
- **Nix:** the start inventory records changes to `tools/internal/README.md`
and `tools/internal/nix/prepare.py`, plus the addition of
`tools/internal/nix/test_prepare.py`. The M7 repair defers target execution
observations when release preparation runs on a different system, records that
deferral, and gates the bounded aarch64-on-x86 emulation option explicitly.
Seven focused unit tests passed, as did Ruff, format and Python compilation
checks. The only recorded amd64 regression rerun was:

  ```sh
  python3 tools/internal/nix/sync.py --check \
    --release /tmp/score-m6-nix/release-amd64 --system x86_64-linux
  ```

  It passed with no stale outputs. The full six M6 root gates were not rerun
  against this Nix source change. M6 results remain tied to their recorded
  source hashes; see the [M6 integration comparison](../../../docs/tooling-integration-milestone.md).

The later [independent root review](root-review.json) confirmed these same
source changes after worker completion; no further production source change
was made. Root also independently reran all seven Nix focused unit tests.
The cross-producer repair is a one-time correction, while target closure
production and platform availability checks remain release responsibilities.
Corrected runtime mount/cache/fixture failures were harness setup, not product
capability gaps or recurring platform implementation requirements.

Candidate M7 result JSON carries the source hashes for the exact owners used
and the worker's per-check records. No raw logs, binaries, caches, wheelhouses,
Nix store payloads, or runtime images are archived here. All payloads in this
evidence directory are below 50 KiB.
