<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M7: execute the migrated tool selection on Linux ARM64

Continue all three local M6 candidates equally; no adoption, commits, pushes,
publication, hosted jobs, or changes to tool pins. This closes a known platform
execution gap rather than introducing a new consumer interface.

## Common acceptance boundary

- Prepare the current maintained `published` native/Python selection for
  aarch64-linux using the candidate's maintained provisioning/release APIs.
- Run actual owner-selected tools in a Linux ARM64 container under QEMU, using
  the existing local `score-tooling-reference:final-arm64` image as an OS/runtime
  substrate only (image ID b36448960057f54745f841561338487c5e9e2128526113c24b4861a7cf0f065a).
  The image's old tools are not candidate output: resolve each tested command to
  the new prefix/store, record exact paths/versions/architecture, and fail on
  accidental fallback. No full feature-image or native ARM hardware claim.
- Exercise uv, uvx, Ruff, pre-commit and the remaining selected migrated
  commands; include Ruff's real failing diagnostic, a Python CLI behavior, and
  direct/strict invocation where supported. Run prepared tools as non-root,
  offline, without manager/Bazel invocation. A native manager is allowed while
  provisioning, never required per prepared call.
- Repair actual source defects and add relevant regression coverage, preserving
  the amd64 contract. Record upstream package/platform gaps explicitly; do not
  silently omit a selected tool or invent new support promises.
- Inspect the existing macOS ARM declaration for obvious mismatches and document
  which selected tools are supported/limited. Config or evaluation is not actual
  macOS execution. Do not add speculative platform abstraction layers.

## Ownership and resource limits

Each codex-1 worker owns its existing candidate worktree and `/tmp/score-m7-NAME`.
Root owns comparison documents and the shared contract/evidence. Preserve all
inherited changes. Read other candidate source if useful; do not edit it. No
nested agents/CLIs, global Docker prune, full image builds, or large runtime
copies. Use unique `score-m7-NAME-*` task containers and label them
`score-m7-platform.candidate=NAME`; keep output under about 3 GiB per candidate
and stop allocation before free disk drops below 4 GiB. Reuse caches safely.
Do not change the shared Nix producer owner concurrently with another worker.

Write progress early and update after meaningful findings. Add a candidate
`README-m7.md` and a compact JSON report with exact commands, results, executable
paths, runtime/network/user conditions, owner versions and source hashes.
Separate one-time repairs, recurring per-tool metadata, shared SCORE policy,
manager-native mechanisms and external platform limitations. Keep failed attempts
as evidence without counting them as passes. No LOC/time ranking or invented
migration percentage. If a genuine external blocker remains, finish other
independent acceptance and document precise evidence rather than claim success.
