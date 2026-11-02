<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M8: one complete local release and user update

Continue the three maintained M7 candidates equally. No adoption, commits,
pushes, PRs, hosted jobs, public package names or publication. Preserve dirty
work and recorded M6/M7 pins. This is the local end-to-end maintainer/release/user
workflow, not another isolated format or feasibility demonstration.

## Same requested operation

For each candidate produce local release A from its current owners, then request
Ruff 0.14.6 and produce release B (fixture versions 0.8.0 and 0.8.1). This target
is already known from earlier experiments to exist in a historical Nixpkgs
snapshot; record using that prior knowledge instead of claiming new version
search is free. Do not update unrelated tools or edit a second Ruff pin. An
independent locked Nix input for Ruff is allowed and must be accounted for.

Use isolated copies of the current maintained source/owners for the version
change so accepted worktree pins remain unchanged. Execute maintained tools,
not historical experiment generators. Real source/API repairs belong in the
candidate worktree and must also be exercised in the copies. Copies contain
only needed maintained sources and small configuration, never old runtime trees.

## End-to-end acceptance

1. Record the exact authored owner diff and maintainer commands. Immediately
   after the version edit, demonstrate stale derived outputs are rejected;
   refresh them through maintained APIs and show check is clean. Preserve
   unrelated tool selections. Record remaining manual translations/exceptions.
2. Build ordinary wheel releases A and B from the owner-derived metadata with
   explicit release identities and the same candidate-local package name.
   Bind each artifact to its owners/versions. A stale A release must not pass
   current-B validation. Keep local artifacts in a handoff directory outside
   the source tree. No producer manager or experimental source is needed by
   the independent Python consumer.
3. A normal independent uv project first selects A[ruff], then changes only
   the facade release requirement to B[ruff], locks/syncs in the same project,
   and invokes real Ruff. Inspect wheel Requires-Dist and both uv.lock states.
   Execute ordinary uvx with A and B. Consumers never manually copy a Ruff pin
   or use a SCORE wrapper. Include Ruff's expected failing diagnostic.
4. Reprovision the same user-owned native prefix/profile from A to B through
   maintained provisioning APIs. Prove the selected Ruff changes, unrelated
   commands remain selected, and prepared direct/strict invocation uses the
   new pin without manager/Bazel resolution per call. Reuse manager caches;
   there is no need to reinstall unchanged runtime trees.
5. Validate generated simple Bazel artifact selection and execute the updated
   public Ruff target through the existing Bazel interface (at least release B),
   reusing task caches and recording argv/cwd/nonzero behavior as relevant.
   Bazel here is an explicit compatibility consumer, never the ordinary uv
   or native runtime dependency. No new complex Bazel packaging.
6. From the working workflow, remove only demonstrably obsolete helpers or
   instructions in that candidate's maintained release/update path, consolidate
   redundant required steps where appropriate, and document the final supported
   sequence. Do not add a generic orchestrator merely to conceal separate steps.
   Preserve compatibility and evidence; do not delete historical reports.

## Comparison and resource discipline

Each codex-1 worker owns one existing candidate worktree and /tmp/score-m8-NAME.
Root owns this contract and the root comparison/evidence archive. No nested
agents/CLIs; peers are read-only. Keep production references to experiments
absent. Source fixes require targeted tests; rerun affected checks, not full
images. Native ARM, macOS and hosted release remain outside M8.

Disk is constrained. Root removed obsolete ARM payloads and obsolete M2 image
tags, preserving reports/source and current amd64 caches. Reuse M5/M6 caches,
Nix producer and immutable closure files without large duplicate releases.
Check df before allocation; keep global free space above 4 GiB. No global prune,
whole-home searches, image pulls or full feature builds. Prefer small artifacts,
hardlinks for immutable payloads, or direct existing producer profile/store
operations. Never modify old accepted release metadata through shared inodes.

Write progress early, final.md and compact result.json under /tmp/score-m8-NAME,
and a durable README-m8.md in the candidate reference directory. List exact
commands and failures with causes, authored versus generated diffs, API/source
fixes, artifact and source hashes, consumer prerequisites, and a responsibility
ledger. Separate one-time repair, per-version edits, per-release operations,
per-platform recipe work and user update actions. Explain what can actually
be removed and what remains. No prototype LOC, wall-clock time or green-cell
count scoring; no claim of completed whole migration.
