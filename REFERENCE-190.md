<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Issue #190 reference: aqua

Alternative evaluation reference. Frozen snapshot of the existing local work on 2026-11-02.
This branch preserves a development/evaluation reference, not a production release
or a claim that every platform gate has passed. Do not merge this branch wholesale.

## Decision and reference map

[Issue #190](https://github.com/eclipse-score/devcontainer/issues/190) records the current decision: consolidate our own
provisioning; Aqua and mise remain comparison evidence, not maintained production
alternatives. The issue and this reference entry point supersede older statements
in exploratory documents that the choice is still open or all work remains local.

- [own-provisioning](https://github.com/eclipse-score/devcontainer/tree/reference/190-own-provisioning) — Selected implementation reference.
- [aqua](https://github.com/eclipse-score/devcontainer/tree/reference/190-aqua) — Alternative evaluation reference.
- [mise](https://github.com/eclipse-score/devcontainer/tree/reference/190-mise) — Alternative evaluation reference.
- [decision-and-evidence](https://github.com/eclipse-score/devcontainer/tree/reference/190-decision-and-evidence) — Decision, comparison and cross-variant evidence.

The decision-and-evidence branch contains the latest cross-variant documentation.
Variant-local copies of comparison documents may be older. Some recorded evidence
references local caches, paths or runtime payloads which are not part of Git.
Publishing the source/evidence snapshots does not publish those runtime artifacts
or establish a hosted release or fully reproducible acquisition environment.
Full ARM64 image and actual macOS ARM validation remain open.

## Extracting the next PRs

1. Start each PR from current upstream `main`, or from an explicitly dependent PR.
2. Use the frozen own-provisioning implementation as the source of the relevant
   behavior; use Aqua/mise for comparison where useful.
3. Adapt the selected change to the current code and preserve callers. Copying
   exploratory commits wholesale is not the intended PR boundary.
4. Record the reference commit and the behavior extracted in the PR or #190.
5. Validate the resulting PR independently; historical tests cover their recorded
   source snapshots, not every later combination of extracted changes.

[PR #196](https://github.com/eclipse-score/devcontainer/pull/196) is the first extraction: shared catalog reading at
`tools/internal/catalog.py`, with definitions left in place. Experimental paths
such as `tools/score_tools/` in these references are not a decision to restore that
package name. Adapt follow-up work to the structure actually landed upstream.

Keep these branches frozen: no force-push, rebase or deletion during the migration.
If a new reference is needed, create a separately named successor and link both
commits in #190. Fixed commit links in the issue retain the snapshot identity.

## Reading the implementation and evidence

Start with `docs/tooling-own-provisioning.md` on the decision-and-evidence branch
for the selected implementation, then `docs/tooling-direct-comparison.md` and
`docs/tooling-effort-conclusion.md` for the comparison. The same branch holds the
decision record and `experiments/tool-manager-comparison/` evidence.
Variant-specific experiments and tests are retained on their respective branches.

`docs/tooling-pr-sequence.md` is a historical breakdown, not an up-to-date promise
of exact PR count, names or file paths. Reconcile each next boundary with #190,
PR #196 and current upstream before implementing it.

Snapshot parent: `2e337e41fba86ea7a94ee3d5e58cf3c4f7d93561`. The worktrees and their existing uncommitted
changes were preserved; this archive was created using a separate temporary index.
