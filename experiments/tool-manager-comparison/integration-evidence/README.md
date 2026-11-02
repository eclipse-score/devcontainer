<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M6 comparison evidence

Point-in-time evidence for the [M6 comparison](../../../docs/tooling-integration-milestone.md), captured on 2026-11-02. Candidate source inventories and audits are from the stable M6 worktrees. Root integration results and final runtime proofs are recorded separately from worker handoffs.

## Current integration outcomes

All six latest actual root results passed: three generic Node lifecycle checks and three fresh amd64 builds with the existing full feature suite. The build output was cache-only; no published image was loaded or launched. The concise [root gate report](integration-gates-final.md) identifies each run. The exact final results are [Mise lifecycle](mise-node-lifecycle.final-result.json), [Mise build and feature suite](mise-published-amd64.final-result.json), [Aqua lifecycle](aqua-node-lifecycle.final-result.json), [Aqua build and feature suite](aqua-published-amd64.final-result.json), [Nix lifecycle](nix-node-lifecycle.result.json), and [Nix build and feature suite](nix-published-amd64.final-result.json).

Historical lifecycle and published-gate failures, plus an interrupted Mise retry, are preserved as separate result JSON files. See the root gate report for the source-versus-harness causes and corrections. They are not counted as current passes.

## Contents

| Evidence | What it records |
| --- | --- |
| [Mise worker handoff](mise-worker-report.md), [Aqua worker handoff](aqua-worker-report.md), [Nix worker handoff](nix-worker-report.md) | Candidate source changes and local checks at worker handoff time. These reports predate some root-owned integration results; the result records above are authoritative for root gates. |
| [Mise lifecycle fix](mise-lifecycle-fix-coordinator.md), [Aqua lifecycle fix](aqua-lifecycle-fix-coordinator.md), [Aqua bootstrap review](aqua-bootstrap-review.md) | Source-level lifecycle and early bootstrap corrections. |
| [Mise mode audit](mise-mode-cleanup-coordinator.md), [Aqua mode audit](aqua-mode-cleanup-coordinator.md), [Aqua helper mode fix](aqua-exec-mode-fix-coordinator.md) | Shebang executable-mode cleanup and the Aqua Dockerfile helper correction. |
| [Aqua selected-output exposure fix](aqua-exposure-fix-coordinator.md) | Regression and real cached-manager checks after unselected gh output shadowed the expected APT command. |
| [Aqua same-prefix retirement proof](aqua-native-same-prefix-retirement.md) | Actual Aqua 2.65.2 and uv 0.13.6 reprovision retired owned Buildifier and preserved a user replacement and unrelated sentinel. Cross-profile and alias/symlink cases remain fixture-only. |
| [Nix Ruff consumer proof](nix-ruff-consumer.md) | Ordinary local-wheel Ruff consumption via uv and uvx; no Nix runtime required for the consumer. |
| [Nix release preparation](nix-release-coordinator.md) | M6 package binding, owner validation, and closure reuse; not an image-build result. |
| [Final Aqua gate coordinator report](integration-gates-aqua-exposure-coordinator.md), [root gate summary](integration-gates-final.md) | The latest Aqua full-gate pass and final six-result scope, with historical attempts distinguished. |
| [Mise prepared runtime checks](mise.runtime.json), [Aqua prepared runtime checks](aqua.runtime.json), [Nix prepared runtime checks](nix.runtime.json), [runtime context](runtime-context.json) | Five direct-versus-strict checks per candidate under poisoned PATH, including Ruff's nonzero exit and a filename containing spaces. Actual tools ran and no manager/Bazel interception marker fired. Nix used a validated M6 store read-only, network-disabled, as uid 1000; this is not a host-bootstrap or full-image claim. |
| [Mise source audit](mise.source-audit.json), [Aqua source audit](aqua.source-audit.json), [Nix source audit](nix.source-audit.json) | Regenerated independent audits: old native installation definitions and commands absent; no production references into experiments. The remaining install.py applies selected APT/npm providers and exposes environment/feature metadata and selection queries. |
| [Maintained-source inventory](maintained-source-sha256.json) | Final maintained content hashes and executable paths. It includes the final Aqua exposure helper/test content and mode inventory. |
| [Provenance](provenance.json) | Source paths/digests, final archived digests, and archive transforms. SPDX headers or JSON license sidecars are present. |

M6's shared package contract is an explicit release version plus configurable package identity. A name may have a default; local checks that supplied names do not prove a universal mandatory name argument. Package identity, public hosting, and hosted release process are undecided. No candidate was adopted.

The managerless control has not implemented M6's maintained package generation, deselection handling, and equivalent local-wheel flow. This archive does not establish equivalent control maturity or prove that a manager is cheaper. ARM Linux, macOS, hosted release, and loaded-image execution were not verified. No raw command logs, full build contexts, or runtime payloads are included.
