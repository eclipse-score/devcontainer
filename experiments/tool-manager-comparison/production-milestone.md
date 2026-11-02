<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Milestone 3: integrate prepared tools into the actual published DevContainer

Continue mise, aqua/uv and Nix equally, locally. No manager selection, push,
publication or PR. This milestone replaces further isolated tool probes with
integration into the real S-CORE image and existing local features.

## Same outcome for all three

1. Extend the existing candidate producer and checked-in integration. Stage a
   fresh published prepared runtime and current compatibility metadata for the
   actual `src/s-core-devcontainer/.devcontainer` build. Use current native
   owners, existing public commands and generated data. No hand-maintained
   duplicate version/membership list or consumer manager requirement.
2. Wire the real Dockerfile/local-feature installation to use those prepared
   native/Python tools. Prevent the old environment installer from downloading
   or reinstalling tools already supplied by that prepared runtime. Retain all
   APT/build/cleanup phases and unmigrated native/setup paths. A small generated
   handoff manifest/installer is acceptable; it is an output, not a universal
   authored schema. Fail clearly if declared prepared tools are missing or stale.
   Do not merely overlay an old full image or leave two competing installations.
3. Preserve existing common-utils/LLVM features, production user, system CA,
   CodeQL/packs, Bazel lifecycle/completion, APT packages, cleanup and environment
   setup. Keep complex tools outside new Bazel packaging. apm/opencode/starpls
   and special providers may remain on existing paths in this bounded step.
   Preserve existing version-owner distinctions; the production Bazel selection
   is still its explicit provider policy, not an accidentally selected latest.
4. Actually build the full local Linux amd64 DevContainer from the modified
   production source/config, including its normal feature chain. Use isolated
   candidate tags/build state. A locally installed devcontainer CLI or an
   isolated `npx @devcontainers/cli` is allowed; do not alter global installs,
   credentials, the shared buildx builder or unrelated running containers.
   Preserve proxy behavior and pinned feature locks. Standard Docker caching is
   allowed; replacing the full build with an old-image overlay is not.
5. Run the existing test-project/test.sh inside that full image as vscode with
   its real feature tests and metadata. Some original tests download source
   packages/network resources; run those online as designed. Separately verify
   selected prepared commands, useful Ruff/pre-commit/pytest/basedpyright
   behavior, both existing run-tool container modes, and preinstalled Bazel with
   network denied as the real non-root user. No producer-manager/cache bind
   mounts for runtime tools. Do not claim the complete test suite is offline.
6. Prove provider handoff is real: retain build evidence that selected native/
   Python installs are skipped because a verified prepared runtime supplies them,
   while original APT/unmigrated paths still execute. Add focused regression
   coverage for that skip/validation boundary and stale/missing handoff failure,
   not a new general testing framework. Existing root metadata/drift and tool
   documentation checks must still pass. Keep compact source/build/test evidence.

## Coordination and honest limits

Each CLI worker edits only its own existing sibling worktree and task-specific
temporary paths. Read the other two implementations for useful fixes; report
cross-cutting findings in a small progress file for the coordinator to relay.
Workers are already launched through codex-1: do not invoke nested Codex, create
more agents, reauthenticate or modify global configuration. Do not commit
inherited uncommitted docs, push, publish, merge or send external messages.

Record progress under /tmp/score-m3-CANDIDATE/progress.md and a final report in
the worktree reference directory. Preserve milestone-one/two evidence/history.
Tag images score-CANDIDATE-m3:local-amd64; use candidate-specific Bazel/cache
paths. Stop only task-owned producer/test containers when finished.

If an unchanged external feature/package/artifact blocks a full build or test,
report the exact failing command, pin and underlying error early. Diagnose it
and distinguish candidate integration defects from baseline/environment issues;
do not silently remove a feature, relax a pin/test or label a partial image as
complete. Ask the coordinator to align any shared adjustment across all three.

Arm64/macOS execution, the Node/Docker outer development container, complete
native-catalog migration, automated release/update jobs and archival remain
outside this checkpoint. Nothing here establishes an overall migration percent.
