<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M5: retire the replaced installation engine in all three variants

This is implementation, not another feasibility probe. The three existing
candidate worktrees have the same outcome contract. All work remains local;
no commits, pushes, PRs or publication. Existing dirty M1–M4 changes are inputs,
not disposable edits. The root comparison checkout remains the managerless control.

## Required final behavior

1. Provision every declared native and Python selection from the candidate owner,
   including starpls, codespell, APM and OpenCode. Preserve existing owner-selected
   versions and ordinary uv/uvx dependency consumers. No new Bazel packaging of
   complex tools. Nix may use the verified small binary OpenCode derivation;
   its source-build fallback is not mandatory.
2. Migrate feature runtime provisioning and root post-create/repository setup.
   Default image builds must prepare their own required inputs, rather than
   depend on an unmentioned manually generated handoff. APT, optional external
   features, provider metadata, NPM and lifecycle duties remain explicit.
3. Remove the obsolete native download/extraction and Python-tool installation
   implementation and CLI subcommands from tools/internal/devcontainer/install.py,
   after migrating every active caller. Remove dead fallback branches and helpers;
   do not merely leave the old engine installed but skipped by a manifest.
   Reconsider temporary handoff validation when it no longer protects a real
   boundary. APT/environment verification may remain in that module.
4. Preserve public Bazel labels and runner argument/cwd/exit contracts. Keep the
   needed generated portable URL/hash/layout metadata and its exporter. Provide
   an explicit host provisioning path plus direct pinned execution after it;
   normal prepared calls must not resolve/install/evaluate a manager or Bazel.
   Containers trust their installed pinned versions. Do not invent a second pin.
5. Update owner refresh/compatibility export commands and the corresponding
   Renovate/daily-job allowlists together. Keep ordinary package/extra metadata
   and release generation usable locally; configure publication if needed but
   never execute publication. Remove stale production docs and obsolete tests
   without weakening behavioral coverage.
6. Execute meaningful current checks: caller/removal audit, selection/export
   freshness, native/Python behavior and ordinary dependency/uvx consumer, public
   Bazel compatibility, host direct path, feature/post-create integration and a
   fresh full Linux amd64 image when feasible with available caches. Platform
   support claims must distinguish declarations, builds and actual execution.

## Comparable deliverable

Each candidate writes a local M5 report in its reference directory, with exact
commands/results, remaining limitations and a maintenance ledger:

- What old responsibilities/code were actually removed, and which callers moved?
- What candidate installation/bootstrap/export/runtime responsibilities remain?
- Which adapters are shared policy versus tool-specific exceptions?
- Which work is one-time migration versus recurring tool/update/release work?
- Which checks ran against the final files, and which did not?

Do not rank by prototype LOC, experiment/evidence file counts or elapsed agent
time. The root agent will audit live callers and inspect the surviving runtime
code across all three, then update the comparison from the actual final states.
Historical experiment reports may mention removed APIs; they are not live callers.
