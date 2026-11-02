<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Round 3: one Ruff update, three delivery consumers

2026-10-31. All three candidates use the current decision-record U5 requirement.
This is a bounded file-design and actual-consumption probe, not three production
implementations. No global installation, publication, production edits or broad
new tests. Keep prior comparable results; do not count unattempted work as an
intrinsic inability.

## Shared outcome

A maintainer changes one authoritative Ruff version selection. Native/container
provisioning, retained simple Bazel metadata and a normal uv package dependency
all derive the same version. An independent uv consumer and uvx invoke real Ruff
without a custom runner or the producer's package manager. An optional score-tool
command is permitted but cannot substitute for resolver-visible dependencies.

Use existing versions/inputs when possible. Nix may select a different published
package-set revision; do not force historical recipe construction. Equal tool
versions suffice; platform artifacts and runtime closures may differ. Ruff's
normal PyPI distribution is an allowed uv delivery path despite native archive
provisioning elsewhere.

## Minimum evidence

1. Record authoritative before/after inputs and diffs; identify every manually
   edited selection versus generated data. Release fixture package versions may
   differ and are not a second maintained Ruff pin. No native/Python owner pair
   with independently edited Ruff versions.
2. Show actual native Ruff version and matching generated Bazel version/artifact
   selection for both states. Reuse earlier install/export tools and runtime
   proof. No full production image/Bazel rebuild required; distinguish generated
   metadata from an executed Bazel target.
3. Produce ordinary Python distribution metadata declaring Ruff as a dependency,
   e.g. optional extra. Distribution/extras names are experiment choices, not an
   adopted API. Generated static metadata with an ordinary build backend is fine;
   no producer manager required by the consumer/build unless explicitly accounted
   for. Keep requirements-only exports separate: they do not establish this case.
4. In a temporary consumer project, use uv to add the release-selected package
   dependency, lock/sync, then execute Ruff. Downstream metadata selects our
   package/release, never a manually copied Ruff version. Inspect uv.lock and/or
   installed Requires-Dist for the actual version selection.
5. Run real Ruff through uvx using the same selected facade/extra (local wheel or
   local Git release allowed). Cover before/after versions. No publication and
   no runtime helper that secretly installs another Ruff environment.

Prefer shared ordinary package mechanics learned from peers. Use local release
fixtures/wheels or independent temporary Git repositories without committing
inherited worktree documentation. Do not impose identical source file syntax,
backend count or package-set shape. Preserve exact commands/results and disclose
untested production release retrieval/packaging details.

## Comparable complexity ledger

For each candidate list:

- Authoritative version and membership decisions, maintained data locations.
- Generated native/Bazel/Python metadata and their refresh/check sequence.
- Permanently owned translators/recipes, including archive layout and exceptional
  Python distribution/entrypoint mapping; identify what upstream already owns.
- Build/release steps needed so ordinary uv consumers see valid dependencies.
- Consumer prerequisites and example native uv/uvx selection commands.
- Separate disposable fixtures/tests from production responsibilities. Do not
  use file counts, prototype LOC, elapsed time or manager branding as scores.

Each agent reads and challenges the other two final round3 reports, exchanging
concrete corrections before the parent synthesizes. An open gap is reported with
its exact scope. No more general capability survey or equalizing test-count race.
