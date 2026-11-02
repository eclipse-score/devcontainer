<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Parallel reference implementations — milestone 1

User direction: continue mise, aqua and Nix equally. No candidate is selected.
The earlier preference is a historical assessment, not an active implementation
instruction. All work stays local in the existing candidate worktrees.

## Result to deliver

A reusable, reproducible local tool-bundle reference for EACH candidate, extending
the earlier single-Ruff probes into the same multi-tool delivery implementation:

- Direct tools: Ruff, ShellCheck and pre-commit. Use existing tested versions;
  candidate-specific published package versions are permitted and documented.
- Two actual selections: `published` has all three; `repository` has Ruff and
  pre-commit. No copied hand-maintained tool version or membership decisions.
- Native source of truth for candidate versions/selections; generated outputs
  may include normal Python package metadata and Bazel artifact registrations.
- A maintained producer entrypoint prepares a self-contained release directory:
  authoritative configs, installer/provisioning entrypoint, generated package
  metadata and a usable minimal Bazel module with public CLI targets.
- Native uv consumers select this release package, using extras for applicable
  Python distributions (Ruff and pre-commit). Normal uv project dependency and
  uvx both work without producer managers or a custom installer at runtime.
  ShellCheck does not need Python delivery merely for artificial symmetry.
- Actual Bazel execution for Ruff, ShellCheck and pre-commit from the prepared
  module. Keep this limited to portable native tools and the existing lightweight
  Python launcher pattern; no complex tool or closure packaging in Bazel.
- A real prepared Ubuntu/non-root/no-network runtime for both selections. Verify
  selected commands, actual versions and absence of the excluded ShellCheck in
  the repository selection. Runtime paths/closures may differ by candidate.
- A real isolated-release update of Ruff reaches native installed selection,
  generated Bazel metadata and the resolved uv package; unaffected direct tools
  retain their selected versions. Keep authored/generated diffs and exact results.

Use the shared `reference-runtime-check.sh` from this directory for both runtime
selections. Supply the profile and actual expected versions via its documented
`SCORE_*` variables; provide a writable home/tmp. Copy the unchanged check into
your reference tests or mount it read-only from this shared directory. The outer
Docker invocation must enforce `--network=none`.

Use the shared Ubuntu base from the previous protocol. It intentionally contains
system Git/Python but none of the candidate tools/managers. Full S-CORE image or
legacy APT/CodeQL migration is not part of this milestone. Existing production
files in the worktree remain baseline unless an isolated candidate reference
file explicitly replaces them. This is production-shaped reference code, not
three unrelated throwaway one-off scripts.

## Structure, evidence and boundaries

Keep new maintained sources under each existing experiment's `reference/`.
Reuse prior working adapters instead of copying many variant scripts. Record
what upstream handles, what we permanently own, what is generated and what only
verifies the reference. One documented prepare/check sequence should reproduce
it; avoid a new custom universal tool schema or publishing framework.

A local temporary Git release repository is allowed for uv/Git consumption;
never commit inherited worktree docs merely to create that fixture. Do not push,
publish, install global managers, change other worktrees or spawn more agents.
Bazel output bases, Docker tags/containers and temp paths must be candidate-specific.
The pinned uv runtime for Bazel may reuse the baseline native uv lock definition;
record its ownership rather than adding an independently maintained version.
No new host Python prerequisite for Bazel CLI consumers.

Use actual caller cwd/arguments/exit behavior and deliberate release selection;
reuse successful hostile-config primitives instead of building a new runner UI.
Both container run-tool modes trust the prepared image's tool versions.

Agents share implementation approaches and cross-review the other two references.
No pass-count winner. If a common scope item blocks one implementation, exchange
approaches and report the exact remaining gap; don't silently reduce that
candidate's scope or build an oversized workaround. End at this same checkpoint
and compare maintained decisions, integration responsibilities and actual gaps.
Mac ARM is artifact/package metadata coverage unless a real Mac is available.
