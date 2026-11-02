<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Milestone 4: compare the cost of onboarding real tools

Implement the same bounded maintainer workflow in the existing mise, aqua/uv
and Nix worktrees. Everything stays local. Preserve milestone 1–3 evidence and
the confirmed native uv/uvx, simple-tool Bazel and container trust boundaries.

## The same change request

1. Move existing **starpls** from its legacy-only download into the native
   published selection. Existing `//tools:starpls` and the Bazel feature retain
   their identities. mise/aqua can retain the current 0.1.22; Nix may select its
   locked native package version, with the difference explicit. Do not describe
   starpls as a Python distribution or invent a corresponding facade extra.
2. Add **codespell** as a representative Python CLI in the published selection
   and `s-core-local` Python composition. This is an experiment fixture, not a
   proposal to add a new repository lint policy. mise/aqua can pin 2.4.1; Nix may
   follow its locked package. Version ownership stays native and singular.
3. The smaller `repository` selection stays unchanged: neither new tool is
   added there. Published package consumption gains a normal codespell extra;
   existing consumers must not author a second codespell version.

## Observable completion criteria

- Extend the actual native configs, existing producer/exporter and current root
  compatibility metadata. Record every needed identity/archive/platform adapter
  change. Do not add a generic catalog framework just to make onboarding look
  configuration-only. Preserve matching declared versions across native, root
  Bazel and Python dependency routes where applicable.
- Prepare a fresh immutable release using current owners. Current drift checks
  must pass; the old M3 prepared release must be rejected after the owner change.
  No relabeling old releases. Refresh generated native locks/checksums normally.
- Execute both added commands from the fresh native/prepared published output.
  Exercise an actual starpls initialize/shutdown exchange and a codespell typo
  diagnostic. The shared checker will live in the primary worktree at
  `experiments/tool-manager-comparison/onboarding-runtime-check.py`; coordinator
  will provide its invocation. A native producer container is sufficient: do
  not claim a runtime probe replaces a fresh full production image build.
- Execute actual existing root Bazel labels `//tools:starpls` and
  `//tools:codespell`. Online preparation is allowed; record network conditions.
  Keep Bazel packaging limited to the existing simple executable/Python adapter.
- Build the ordinary facade artifact, inspect its exact Requires-Dist, and use
  real uv project lock/sync/run and uvx with its codespell extra. A real spelling
  diagnostic must work. No wrapper, consumer manager or manually supplied second
  codespell pin. Preserve other published extras.
- Generate/stage the current production handoff. Prove that starpls and
  codespell now take the existing verified prepared-tool skip path and that
  unaffected APT/unmigrated paths remain selected. Extend focused regression
  only where a concrete new boundary needs it. Keep the original legacy starpls
  download as the ordinary unprepared-installer fallback.
- Run current root/tool documentation drift and relevant source checks. Record
  the unchanged repository selection and the rejection of the old release.

The existing full M3 images and tests remain historical evidence. This milestone
does **not** require another complete LLVM/APT/CodeQL image rebuild. New source
selections make old prepared images/releases stale; report that explicitly and
do not describe those images as validated against the new owners. No ARM/macOS
execution, update bot, release publication or whole-catalog migration is implied.

## Compare the maintainer work, not just success

Each worker writes `reference/README-m4.md` and a compact licensed JSON ledger
under `reference/evidence/m4/`. Separate:

1. Authored policy: version/profile choices and public tool identity metadata.
2. Permanent adapter changes: tool-specific knowledge or general integration
   limitations exposed by these additions, with the exact purpose of each edit.
3. Generated outputs: normal commands and resulting artifact classes.
4. Execution: actually observed paths, commands, outputs, blockers and limits.

For each manual edit state whether it is a normal operation for the next similar
tool or a one-time limitation fixed in this implementation. Do not infer effort
from LOC, file count, concurrent wall time or pass counts. A missing native
registry/package is a useful comparison result: investigate the native route and
report the concrete boundary rather than silently substituting a different tool
or forcing complex packaging.

## Coordination

Workers use only their assigned sibling worktree and `/tmp/score-m4-CANDIDATE`.
No commits, pushes, publication, global installs, shared-builder mutations or
unrelated container/cache cleanup. Never search all `/home/alex` or inspect other
trust zones. Use existing task-local tools and pinned native inputs where possible.

Write progress to `/tmp/score-m4-CANDIDATE/progress.md`. **Reread
`/tmp/score-m4-common/coordination.md` before preparation, before acceptance and
before the final report.** Exec CLI queue messages do not steer a running turn.
Cross-read peer M4 changes at those checkpoints, report reusable lessons and edit
only your own files. No nested Codex or additional agents. Keep tool output
bounded: do not print entire source trees, diffs or build logs.
