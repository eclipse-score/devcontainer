<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Direct comparison protocol — 2026-10-31

The three agents mutually reviewed all first-round reports and agreed the checks
below. The first mise recommendation is suspended. Compare observable outcomes
and remaining maintenance, not test counts, one-manager branding, file counts,
prototype line counts, or unattempted integrations.

## Evidence and scope

Use the current primary docs/tooling-decision-record.md. Direct dependencies,
multiple native configurations and matching tool versions suffice. Complex tools
need no Bazel packaging. Container execution trusts installed pins. Reuse valid
round-one evidence; do not repeat successful probes without a concrete gap.

For each check report: exact commands/results; authored versus generated changes;
bootstrap/runtime prerequisites; custom code and ownership; remaining limitations.
Classify tested, source-derived, untested, blocked, or not required. A blocker is
not an automatic technical inability. All peers read and challenge the final
results before parent synthesis. Do not edit another candidate's worktree.

## C1 — Independent maintenance and environment selections

Change one selected tool's actual version while the other direct tool retains
its version. Show authoritative-input and generated-output diffs and how the
selection reaches intended consumers/environments. Reuse prior executed update
proof where it suffices. Nix may use another published locked Nixpkgs input;
no custom recipe merely to match an old version, and no requirement that the
transitive closure stay identical. Separate declaration evidence from actual
execution after the change. Demonstrate selection/add/remove only where prior
proof leaves an open question. Record ordinary maintainer steps, not a new UI.

## C2 — Release-selected execution from a consumer working directory

From a temporary Git consumer outside the config checkout, run the selected
Ruff and pre-commit versions without Container/Bazel for that delivery path.
Put a fake same-name CLI and conflicting consumer manager configuration in the
consumer environment. Confirm that explicit pinned selection wins; preserve
cwd, arguments and exit status. Use an unused-import Ruff fixture (F401, exit 1)
and a local pre-commit system hook that observes the consumer cwd. Both tools
must really execute, not a mock. No requirement to implement the full Git-package
UX. Manager bootstrap is allowed; a generated version export to uv is also valid,
with its extra release packaging/consumer steps reported. Use prepared inputs so
this does not accidentally measure fresh dependency downloads. If a native Nix
host is unavailable, demonstrate a Nix-free exported uv route and mark native
Nix host execution untested rather than silently count Docker as a host probe.

## C3 — Prepared direct execution in a common Ubuntu runtime

Shared base: score-tool-manager-comparison-base:20261031, built by the parent from
the adjacent Dockerfile (Ubuntu 24.04, CA certificates, git, Python3, user 12345).
No Ruff/pre-commit/uv/manager is preinstalled. Verified image ID:
`sha256:1b1ebf493ffb1a5a3a4d3c4c2a822cfe0da563d7028159078b0a02a12122a28d`.
The parent confirmed uid/gid 12345, Python 3.12.3 and Git 2.43.0, with none of the
CLIs or managers on PATH, in a network-disabled base run.
Prepare candidate tools into an image or stable mounted paths with their required
runtime. Execute both tools and the same fixture/hook directly, as uid 12345,
with --network=none and writable consumer/home directories. Do not invoke mise,
aqua, Nix, uv or a bootstrap installer at execution time. Bundled runtimes and
a complete Nix closure are allowed; a standalone ELF copy is not equivalent to
an installed environment. Report setup commands, PATH/prefix, permissions,
retained runtime/store and actual results. This is a small runtime proof, not a
production image rebuild or complete archival certification. Do not copy or
mount another repo's image content. Cached candidate files may be reused.

## Equal treatment of remaining gaps

Retain existing Bazel proof separately: aqua has an actual Ruff Bazel run, mise
has metadata equivalence, Nix has a tested version export. Do not turn that into
a capability ranking. Identify the smallest remaining bridge and share recipe
or export approaches across candidates; no general exporter or complex packaging.
Actual macOS ARM execution remains unavailable for all candidates. No invented
platform guarantee or numerical performance ranking. The unresolved uv-only
interface is evaluated as a choice, not awarded only to one candidate by default.

No global installs, production edits, pushes or publishing. Agents keep follow-up
artifacts in their own experiment directory and discuss findings directly.
