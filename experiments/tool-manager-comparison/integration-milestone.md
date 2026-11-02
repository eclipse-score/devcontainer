<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M6: close the remaining integration boundaries

Continue mise, aqua and Nix equally from their local M5 worktrees. No adoption,
commits, pushes, PRs or publication. Preserve inherited changes. This is actual
implementation and integration verification, not another feasibility round.

## Equal implementation outcome

1. Reprovisioning an existing host selection retires commands removed from that
   selection. Delete only manager/provisioner-owned exposure, preserve unrelated
   user commands and other environment selections, and handle a user-replaced
   command without silently deleting it. mise/aqua need explicit reconciliation;
   Nix should exercise the equivalent current profile replacement behavior.
2. Production compatibility/update/package generation must work without reading
   or writing `experiments/`. Move the ordinary Python dependency-package
   generator/release checks to maintained paths. Keep direct owner pins, standard
   extras and normal uv/uvx consumption, with no required SCORE runner. Use an
   explicit release version and configurable package identity; local candidate
   names are acceptable until adoption. Bind local package/metadata to that
   release and the selected tool versions. Never publish or register anything.
3. Exercise current owners through a locally built wheel and an ordinary uv
   consumer/uvx invocation. Preserve existing Bazel labels and prepared strict
   direct execution/fallback, with no manager or Bazel on the prepared path.
4. Root coordinates disk and serial full-image/root-Node integration gates. Do
   not independently pull generic Node images, run full builds, duplicate
   runtime contexts or prune shared Docker data. Finish the bounded changes and
   checks, provide exact image/lifecycle commands, then hand off a stable source.
   Image failures must be fixed and retried when resources permit.

## Ownership and evidence

Each CLI worker owns one candidate worktree and `/tmp/score-m6-{candidate}`.
Root owns the primary comparison checkout and shared evidence. Other public
candidate source may be read for review but never modified. Do not spawn other
agents/CLIs. `/tmp/score-m4-*` payloads are obsolete and may be removed by root;
do not depend on them. Reuse M5/current manager caches without large copies.

Write progress early and a final `README-m6.md` in the candidate's reference
directory with exact results, remaining gates and a responsibility ledger.
Separate shared SCORE policy, manager-native behavior and tool-specific adapters.
Identify actual changes to one-time migration versus recurring maintenance.
Do not rank prototype LOC, file counts or agent elapsed time. Run checks needed
for new behavior; avoid repeating passed suites without a relevant change.
