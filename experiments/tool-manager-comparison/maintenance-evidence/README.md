<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Milestone 4 evidence

These are local checkpoint copies from the three implementation worktrees on
2026-11-01. The [comparison](../../../docs/tooling-maintenance-milestone.md)
explains the shared acceptance boundary and maintenance findings.

| Candidate | Authored/generated work and execution ledger | Shared prepared-runtime behavior proof |
| --- | --- | --- |
| mise | [Ledger](mise.maintenance.json) | [Proof](mise.runtime.json) |
| aqua + uv | [Ledger](aqua.maintenance.json) | [Proof](aqua.runtime.json) |
| Nix | [Ledger](nix.maintenance.json) | [Proof](nix.runtime.json) |

The runtime JSON files are actual outputs from the same
[checker](../onboarding-runtime-check.py), using fresh absolute command paths.
They preserve stderr, including the offline background BCR lookup failures.
The outer Docker network settings are recorded in the ledgers; the checker
itself records the effective UID but does not attest network isolation.

Ledger references to additional candidate-specific files are relative to each
original `experiments/tool-manager-{mise,aqua,nix}/reference/evidence/m4/`
directory, not this checkpoint directory. The implementation worktrees are
siblings of the main checkout named `score_devcontainer-eval-{mise,aqua,nix}`.
Their `reference/README-m4.md` files describe reproduction and individual edits.
Temporary release paths document local execution; they are not published
artifacts or portable installation instructions.
