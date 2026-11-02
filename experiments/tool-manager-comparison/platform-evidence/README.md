<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M7 platform evidence archive

This archive records the three completed candidate handoffs for the Linux
ARM64 platform comparison. It keeps compact worker reports, candidate README
copies, the shared substrate probe, the M7 start-source hash inventory, Nix's
macOS package metadata inspection, and the subsequent independent root source
review and common ARM execution checks. The provenance manifest records the
source path and SHA-256 for copied artifacts, the archived SHA-256, and any
SPDX-header transformation.

## Current common root evidence

The [independent root review](root-review.json) confirms unchanged Mise/Aqua
maintained source and the bounded Nix source repair. Its common ARM launcher
test executes all three selected Bazelisk binaries with a fallback refusal
guard; it establishes neither a standalone self-version nor a Bazel engine run.
Together with the worker checks, this covers the common 15 identities for every
candidate, plus Aqua's two extra aliases.

- Mise [Bazelisk guard](mise/bazelisk-guard.json) and
  [five direct/strict cases](mise/root-runtime.json).
- Aqua [Bazelisk guard](aqua/bazelisk-guard.json) and
  [five direct/strict cases](aqua/root-runtime.json).
- Nix [Bazelisk guard](nix/bazelisk-guard.json) and
  [five direct/strict cases](nix/root-runtime.json).

All 15 direct/strict cases passed. Normal direct tool invocation needs no
wrapper; strict runner invocation is an optional compatibility verification.
The earlier worker handoffs below are preserved unchanged apart from SPDX
headers. Their narrower Bazelisk findings are superseded at the guarded
launcher boundary by these root checks.

## Candidate evidence

- [Mise result](mise/result.json), [handoff](mise/final.md), and
  [candidate README](mise/README-m7.md).
- [Aqua result](aqua/result.json), [handoff](aqua/final.md), and
  [candidate README](aqua/README-m7.md).
- [Nix result](nix/result.json), [handoff](nix/final.md),
  [candidate README](nix/README-m7.md), and
  [macOS ARM metadata](nix/macos-arm-package-metadata.json).
- Shared [ARM64 substrate probe](substrate.json) and
  [M7 start-source inventory](source-before.json).
- Independent [source-change summary](source-change-summary.md).
- [Provenance and hashes](provenance.json).

The candidate README and worker-handoff copies may mention absolute paths under
`/tmp/score-m7-*` for transient commands and logs. Those payloads are not copied:
the structured result JSON and handoff preserve the relevant outcomes without
archiving large logs or runtime files. QEMU is emulation, not native ARM
hardware evidence.

Task containers may be removed after validation. Prepared prefixes, source and
caches are retained; worker commands using `docker exec` may need their task
container recreated. The root JSON contains fresh `docker run --rm` commands
and exact mount/runner paths. Their referenced checker scripts remain at the
recorded source paths; their hashes are captured as reproduction inputs in the
provenance manifest.
