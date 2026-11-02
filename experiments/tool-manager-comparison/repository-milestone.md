<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Milestone 2: migrate a real repository toolchain in all three worktrees

User direction: implement a substantial further slice equally in mise, aqua and
Nix, retaining comparability. This is a concrete scope, not a measured 20 percent
of total migration effort. No pushes, PRs or publication; no manager selected.

## Deliver the same outcome

1. Expand the native owner to the actual repository toolset: actionlint,
   bazelisk, buildifier, Ruff, ShellCheck, uv/uvx, yamlfmt, and pre-commit. These
   command names match baseline `tools/environments.json/repository`; uv/uvx
   share a release decision. Include pytest and basedpyright in the broader
   published selection through ordinary Python package delivery, relevant to
   #189. Repository excludes these two extra tools. Versions may follow available
   upstream candidate packages, with exact selected versions recorded.
2. Extend the existing maintained producer, not a second toy implementation.
   Native configs remain version owners. Normal Python extras cover Ruff,
   pre-commit, pytest and basedpyright. Prove ordinary uv resolution, real CLI
   execution and one useful pytest/type-check fixture. No artificial Python
   packaging of native-only tools. Complex Python tooling need not gain new
   Bazel targets merely for symmetry.
3. Integrate into the REAL checkout: generate/update the existing selected
   `tools/lockfiles/*.lock.json`, `tools/score_tools/python_tools.bzl` and the
   repository native/Python fields of `tools/environments.json` from native
   owners, preserving metadata/public labels, npm and unmigrated selections.
   Existing root MODULE/BUILD consumers must execute the candidate-owned
   selections, not only an isolated release-module fixture. Checked-in generated
   snapshots are acceptable; label ownership and provide a regeneration/drift
   check. Remove conflicting direct update rules for generated pins. uv's Bazel
   helper is now derived from the same native uv owner, not a second pin.
4. Build a real local Ubuntu image containing the selected runtime files through
   the maintained installer. A Dockerfile may reuse the shared clean Ubuntu
   base; it must COPY/provision the release, not use producer-cache bind mounts
   as its tool installation. Both selections must be usable as uid12345 with
   network denied and no producer manager on PATH. uv/uvx are now intentionally
   delivered tools, so milestone 1's no-uv/absent-ShellCheck fixture is historical.
   Do not replace the production Node/Docker outer devcontainer or claim full
   production-image migration for this Ubuntu tooling layer.
5. Exercise actual repository consumers: root Bazel targets for the repository
   tools; real `tools/run-tool` convenience/strict behavior using selected image
   PATH; and the existing pre-commit configuration on representative REAL repo
   files covering Ruff, ShellCheck, yamlfmt, buildifier and actionlint. Prepare
   hook dependencies online first if needed. Prefer testing the local hook IDs
   directly rather than silently skipping failing hooks or rewriting policies.
   Global bzlmod checks can run separately with candidate-specific output bases;
   explicitly report full-suite gaps. Full offline cold Bazel/remote-hook setup
   is not required. Never run inherited `--all-files` over all accumulated
   historical experiments and turn unrelated fixtures into migration work.
6. Keep the Ruff independent-update proof through the same maintained paths.
   Demonstrate generated root metadata/uv dependency drift checks detect stale
   output after an owner change, then regenerate. Preserve compact authored and
   generated diffs plus actual command/version/status evidence. Sources and
   generated snapshots should pass applicable formatting/lint/license checks.

## Coordination and limits

Each agent edits only its existing candidate worktree, including the named real
repository consumers there. Primary records the common protocol and synthesis.
Share mapping, image assembly and consumer integration fixes directly while
working, and review peers' final diffs, not only reports. Do not create new
agents, frameworks or global installations. Use candidate-specific Docker tags,
Bazel output bases, caches and temporary directories. Stop producer containers
when done; retain only compact reviewable evidence in source directories.

OS APT/feature ownership, LLVM/Rust/CodeQL and remaining native tools are not
migrated in this step. No full production image, all-platform execution, remote
CI run, archive service or public release is promised. Report real blockers
early; don't quietly narrow one candidate or invent large custom packaging to
preserve a green table. macOS ARM remains metadata unless actually executed.

At completion compare what now changed outside experiments, retained adapter
responsibilities, newly discovered obstacles and what remains before actual
adoption. No success-count or LOC winner, and no invented overall percentage.
