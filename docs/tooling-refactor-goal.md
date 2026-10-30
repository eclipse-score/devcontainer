<!--
*******************************************************************************
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0

SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
*******************************************************************************
-->

# Goal: consolidate tool management and prove all three delivery paths

This document defines the scope and acceptance criteria of the local `/goal` run.
The work stays local until explicitly authorized otherwise. The
[reference implementation](tooling-reference-implementation.md),
[completion audit](tooling-completion-audit.md) and
[proposed PR sequence](tooling-pr-sequence.md) record its results.

## Objective

**Build and validate a complete local refactoring of tool management across this
repository, including the uv delivery proposed in #189. Then identify small,
independently reviewable PRs that lead to that proven end state.**

The work covers the architectural consolidation discussed in #190 and a working
implementation of #189. Develop and test them together so that the new delivery
path influences the architecture before it is considered complete.

The [status quo](tooling-status-quo.md) is the baseline. The
[target design](tooling-target-design.md) explains the architectural direction.
This goal document takes precedence where the earlier design draft describes a
narrower implementation scope or a different order of work. Existing GitHub issue
wording is context; it does not override the scope agreed here.

## Desired end state

For every explicitly managed development tool or build helper:

- Its source, version policy, platform support, and update ownership are clear.
- Each version decision has one authoritative source.
- Environment selection is maintained once and reused by installation,
  availability checks, and documentation.
- Installation defines required paths, permissions, dependencies, and setup.
- Checks inspect the actual installed result against the declared policy.
- A generated overview makes its ownership, constraints, environment membership,
  and supported delivery paths discoverable.

The model covers native downloads, APT packages, external feature bundles, and
Python tools. Container-only tools and build-only helpers are included. It does
not require every tool to support every delivery path or one universal file
format or installer.

## Architectural direction

Separate these responsibilities:

| Responsibility | Owns |
| --- | --- |
| Tool definitions | Identity, description, provider, version policy, platform support, and provider metadata |
| Environment composition | Tool or bundle selections for the published image, local features, and repository development container |
| Installation and execution | Provider-specific installation and supported ways to run a tool |
| Verification and inventory | Checks of actual behavior and a generated view of definitions and selections |
| Updates | Changes to the authoritative sources and refresh of derived data |

Retain backend-specific mechanisms where appropriate. Derive repeated lists or
validate unavoidable explicit registrations against the owning data. Generated
copies are acceptable; independently maintained duplicate pins are not.

Use the implementation to settle module boundaries, storage formats, and shared
interfaces. Evaluate the model against ShellCheck, APT tools, LLVM, CodeQL, Bazel,
Python tools, and build helpers. Revise abstractions that do not fit these cases.

Distinguish requested constraints, resolved versions, and independent compatibility
expectations. Preserve the differences between artifact checksums, APT constraints,
feature digests, and top-level Python pins. Do not claim full environment locking.

## Include #189 as a working use case

Implement a Python package that can be invoked through uv from a selected Git
release, without publication to PyPI and without requiring Bazel or a container.
It packages and consumes the same Python tool definitions used by the other
delivery paths. It does not import the container installer or introduce another
parser, package pin source, or downstream requirements file.

The caller supplies compatible uv; the new path does not bootstrap or pin it.
Preserve the catalog-pinned uv runtime for existing container/Bazel delivery and
the ability to start Bazel CLI targets without host Python.

Consolidate the existing uv-installed Python CLIs into shared definitions and a
consistent container installation policy. Demonstrate a real `pre-commit` invocation
through container, Bazel, and standalone uv delivery using the same package version
and entrypoint. Verify arguments, working directory, and exit-status behavior at
the relevant integration boundaries.

Exercise package installation from a local Git reference and verify the packaged
catalog is available outside the source checkout. This proves Git-based delivery
without pushing a branch or publishing a release. Document the corresponding
release-based consumer command for future use; final names follow the implementation.

## Working method

1. Create a separate local implementation branch or worktree and preserve existing
   documentation and unrelated user changes.
2. Build the complete intended arrangement. Use coherent local commits where
   useful, but do not constrain discovery to the final PR boundaries.
3. Validate across providers and all three delivery paths. Update the design as
   the implementation reveals real requirements or unnecessary complexity.
4. Once the end state works, derive a sequence of small PRs from it. Each proposed
   PR must have a concrete outcome, explicit dependencies, and a working state.
5. Record the final architecture, validation evidence, migration implications,
   and PR sequence locally. Keep the complete implementation as the reference.

Do not stop after extracting helpers, writing more design documents, or proving
only the Python case. Small intermediate changes are means of developing the
complete result, not substitutes for it.

## Completion criteria

Verified locally on 2026-10-30. The [completion audit](tooling-completion-audit.md)
records the evidence for every criterion.

- [x] All explicitly managed tools and helpers from the baseline have a place in
  the resulting ownership/composition model, with intentional omissions documented.
- [x] Repeated handwritten version decisions and environment installation lists
  are removed; unavoidable registrations have consistency checks.
- [x] The published image and repository development environment retain their
  intended capabilities, including platform-specific behavior and non-root access.
- [x] Existing native and Python Bazel delivery remains functional without adding
  a host-Python prerequisite.
- [x] Standalone uv delivery works from local Git and includes its catalog in the
  installed package. It requires neither Bazel nor container installation code.
- [x] A real tool invocation demonstrates matching Python package/version/entrypoint
  selection across container, Bazel, and standalone uv delivery.
- [x] Generated documentation, update automation, and meaningful checks consume
  the final authoritative sources and detect relevant drift.
- [x] The invocation/version contract is documented and verified, including PATH
  selection and strict behavior. Existing runner behavior is changed only with a
  deliberate compatibility/migration decision recorded in the local result.
- [x] Appropriate repository checks, affected image builds/tests, and delivery
  smoke checks pass. Record commands, outcomes, and any limitations. Unavailable
  required verification remains outstanding rather than being reported as passed.
- [x] A local PR breakdown describes each change's outcome, dependencies, and
  validation, and leads to the fully implemented reference state. Do not create PRs.

Adding a tool, updating its version, and removing it from an environment must each
have an understandable maintenance path without synchronizing multiple manual
copies of the same decision.

## Boundaries

- No pushes, PRs, GitHub issue edits/comments, package publication, image pushes,
  or releases. Inspect build commands and workflows before running them to avoid
  publication as a side effect. Local commits and local image builds are allowed.
- Downstream workflow migration is documented, not performed in other repositories.
- Full transitive dependency locking, APT snapshots, a formal SBOM, and identical
  image rebuilds are outside this goal. Record the actual guarantees and remaining
  follow-up work.
- Preserve existing tool versions and capabilities unless the refactoring requires
  a justified change. Avoid unrelated upgrades or removal of tools for convenience.
- A full generic installer framework, replacement of `rules_multitool`, and one
  universal command dispatcher are not predetermined requirements.

## Suggested goal instruction

> Implement the complete local tool-management refactoring described in
> `docs/tooling-refactor-goal.md`. Include the standalone uv delivery from #189,
> validate the end state across existing providers and all three delivery paths,
> and derive a small-PR sequence from the working implementation. Follow the
> document's completion criteria and boundaries. Do not push or publish anything.
