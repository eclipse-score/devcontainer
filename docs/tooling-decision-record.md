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

# Decision record: Tool provisioning and version ownership

- **Status:** Requirements partially confirmed — Bazel delivery boundary confirmed; uv integration under evaluation; no architecture selected.
- **Date:** 2026-10-30.
- **Scope:** Tool management in this repository, including the use case in
  [#189](https://github.com/eclipse-score/devcontainer/issues/189) and the
  restructuring discussed in [#190](https://github.com/eclipse-score/devcontainer/issues/190).

## 1. What we want to decide

How should we define the tools we provide, maintain their versions, and make
those tools available to the workflows we actually need to support?

The desired outcome is straightforward: maintainers have an understandable place
to add, update, and remove tools; consumers get the intended versions without
maintaining duplicate pins. We should prefer an established solution when it
makes this easier. A custom catalog is an option to justify, not the starting
assumption.

This record combines confirmed requirements from the discussion on 2026-10-30
with explicitly marked proposals. Multiple backend configurations are acceptable;
we describe direct dependencies, require matching tool versions, and aim to
support macOS on ARM where feasible. Bazel CLI delivery is limited to simple self-contained tools and lightweight
Python delivery; complex tool packaging is excluded. The role of uv and the
choice of manager still need evaluation.

## 2. What is already known, and where it comes from

Different kinds of evidence carry different weight:

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| Direction confirmed in this discussion | Simpler maintenance; multiple configs in one folder are acceptable; normally describe direct dependencies only; equal tool versions suffice; support macOS ARM where feasible | A universal schema, full transitive dependency descriptions, or a particular manager |
| #189, **Use case** | A concrete request to select a DevContainer release and use its Python CLI versions in lightweight CI/local workflows without Container or Bazel; pre-commit drift is the example | Approval of every detail in the issue's proposed solution |
| #190 | Requested continuity of container/Bazel delivery and a truthful pinned-execution contract | That its implementation steps remain the best architecture after this review |
| Accepted upstream decision records | Existing S-CORE constraints and architecture context, summarized below | That this repository must implement every infrastructure responsibility itself |
| [Baseline inventory](tooling-status-quo.md) | What the old setup contains and how it is wired | That every tool, path, flag, or installation mechanism is required |
| [Local reference and validation](tooling-reference-implementation.md) | One implementation can satisfy the previously written experiment criteria | That those criteria are the right product requirements, or that this implementation is the simplest solution |

### Existing S-CORE decisions

The following sources were read on 2026-10-30. The published DR-001 and DR-003
pages were also checked against this record. All three decisions are marked
accepted:

- [DR-001: External development tools](https://eclipse-score.github.io/score/main/design_decisions/infrastructure/DR-001-infra.html)
  makes the DevContainer the primary tool distribution, calls for consistent
  versions, pinned artifacts and an offline/retention path, and explicitly values
  simplicity. Its conclusion prefers native installs for small/fast CI jobs,
  especially where version pinning matters less. Bazel aspects remain appropriate
  for configuration-dependent or cacheable analysis; Multitool is an alternative
  whose maintenance the decision describes as currently infeasible for S-CORE.
  This is not a requirement to distribute every CLI through Bazel.
- [DR-003: DevContainer strategy](https://eclipse-score.github.io/score/main/design_decisions/infrastructure/DR-003-infra.html)
  selects a shared base for development and CI, with optional Dev Container
  features for specialized needs. Ordinary startup should use preinstalled
  tools. It does not prescribe our catalog format or require every tool to
  have a Bazel delivery path.
- [DR-001 extension: Build execution contract](https://github.com/eclipse-score/score/blob/main/docs/design_decisions/infrastructure/DR-001-infra-extension.md)
  adds explicit build contracts: the container is the default, compatible native
  environments are permitted, and compatibility concerns build-relevant
  properties rather than byte-identical environments. Build-relevant tool
  versions must remain reviewable; the container cannot be their only record.

These decisions constrain the discussion. Their application to each tool and
workflow still needs to be made explicit. In particular, release build archival,
Bazel action inputs, container reproducibility, and running a lightweight Python
CLI are related responsibilities, not automatically identical requirements.
A proposal that changes an accepted upstream decision must identify that change.

Consequences for this refactor:

- Keep container-first delivery and direct IDE executable access. The bounded
  Bazel CLI adapter is compatibility work, not a universal delivery requirement.
- #189 fits the native/lightweight workflow direction; its exact uv interface is
  still a separate choice. Do not claim automatic conformance with every DR-001
  reproducibility requirement merely because that workflow is permitted.
- Equal tool versions are the confirmed version-alignment guarantee here.
  DR-001 also requires hash-pinned artifacts, no hidden execution-time fetching
  and an offline/retention path. These remain separate acceptance concerns.
  An initial online install is distinct from prepared offline execution; a
  launcher that may resolve/download dependencies on every run has not yet
  demonstrated that execution contract.
- The choice of package manager must preserve the shared container base and
  feature model. Central tool configuration is another DR-001 concern; selecting
  versions does not by itself solve sharing tool configuration across repositories.

## 3. Proposed requirements baseline

### The outcome in six requirements

The confirmed scope decisions below constrain these proposed requirements.
Details not addressed by the user remain proposals, rather than descriptions of
the local reference's implementation.

| ID | Proposed requirement | Evidence and confidence |
| --- | --- | --- |
| R1 | A maintainer changes a deliberately managed tool version once. Each delivery path derives its selection from that owner; downstream repositories select a release rather than copy individual pins. | Discussion, #189 and #190; high |
| R2 | Keep the published DevContainer as the standard development environment, including direct CLI/IDE access as the non-root development user. Retain existing simple Bazel interfaces; exclude complex tool packaging from Bazel CLI delivery; provide a lightweight path for selected Python CLIs without Container or Bazel. Whether that path specifically uses uv remains open. | Upstream decisions, baseline documentation, #189 and #190; high for workflows, implementation open |
| R3 | A shared tool has the same declared release version across its supported delivery paths. Record exceptions explicitly; do not silently substitute a convenient host version. | #189's pre-commit mismatch and #190; version-level guarantee confirmed in the discussion; full dependency locking is not required here |
| R4 | `run-tool` trusts the tools installed in the selected S-CORE container, including in strict mode. Outside the container, default convenience mode may use PATH; `--strict` selects the release-pinned delivery path instead. Preserve arguments, working directory and exit status. | User-confirmed container trust boundary; refines #190's stronger per-invocation verification wording |
| R5 | Adding/removing a tool declares its intended environments and delivery availability once. Derived registration, metadata and documentation may use multiple files but must not require manual synchronization of repeated selections or pins. | Discussion and #190; avoiding drift and allowing multiple configuration formats confirmed in the discussion |
| R6 | Maintainers can understand an ordinary update and its affected consumers. Prefer an established package/tool model when it reduces custom maintenance; compare ecosystem activity and team familiarity as well as technical fit. | Discussion and upstream simplicity goals; high for goal, team familiarity not established |

### Working defaults for scope and guarantees

Confirmed rows reflect the user's clarification on 2026-10-30. Other rows remain
working proposals; none is inferred as a requirement merely from an old script.

| Topic | Proposed default | Basis and limitation |
| --- | --- | --- |
| Tool scope and authoring | Describe deliberately selected direct dependencies and environment membership. Multiple backend-native configs in one understandable folder are acceptable; there is no requirement for one schema or universal installer. Resolvers may generate transitive locks without requiring us to describe each transitive package by hand. | **Confirmed.** Exact folder layout is an implementation choice. Direct dependencies include intentionally requested OS/runtime packages, not just standalone CLIs. |
| Distribution | Container is the default; Bazel CLI delivery covers simple self-contained tools, with Python delivery only where a lightweight shared adapter suffices. Complex tools need no Bazel delivery path. A lightweight path starts with pre-commit; uv is a candidate interface, not a settled requirement. Do not require every tool on every delivery path. | #189 and #190. Bazel delivery boundary confirmed by the user. Preserve existing simple interfaces; evaluate uv separately (U5). |
| Version consistency | The same declared tool versions across supported delivery paths suffice. Platform-specific artifacts are allowed; tools must run with their required runtime/ABI. Do not require identical transitive dependency or interpreter environments for this change. | **Confirmed.** Existing build archival/provenance obligations still apply in their own scope; equal CLI versions do not claim fully identical environments. |
| Container platforms | Preserve Linux amd64 and arm64 image builds, with explicit per-tool exceptions such as CodeQL's current amd64-only delivery. | Both are in baseline CI. Full downstream build tests currently run only on amd64; arm64 image support does not establish complete downstream support. |
| Host platforms | Support Linux host workflows and target macOS on ARM for applicable host tools as far as feasible. Compare candidates for this use; document per-tool exceptions and validation gaps. Do not require Linux-only tools to become portable. No new Windows or Intel macOS promise. | **macOS ARM direction confirmed.** Existing native metadata includes macOS ARM artifacts. Actual macOS execution remains unvalidated here; define a representative check and record unavailable tools before claiming coverage. |
| Environment selection | Support the published S-CORE environment and this repository's build/test environment. Preserve existing feature composition during migration. Add tool groups only for a demonstrated consumer. | Two distinct environments are documented today. No evidence yet for a general matrix of arbitrary user profiles. |
| Release selection | One repository release identifies the related image and tool definitions; use immutable references for reproducibility-sensitive use. Consumers need not copy each tool's version. | #189 and upstream provenance requirements. A release label identifies related outputs; it does not make independently resolved dependencies identical. |
| Offline and archival | Keep the existing container/build archival contract. This repo supplies immutable references and metadata for the artifacts it owns; deployment/release infrastructure must retain the required artifacts. Standalone installation may fetch initially and must document its resolution/cache limits. | Upstream contracts apply. A fully offline standalone execution guarantee requires a defined prefetch procedure and ownership; that work is not proven complete by version alignment. |
| Updates | Review CLI version changes centrally. Keep OS security updates in their OS backend; an already published immutable image remains unchanged. Refresh locks/artifact hashes where the selected backend supports them. | Proposed separation of tool updates, image construction and historical image retention. Existing APT prefixes are not themselves a requirement. |
| Migration compatibility | Preserve documented command names/Bazel labels and argument/cwd/exit behavior initially. Treat internal paths and scripts as replaceable unless a caller is found. Changed public behavior needs an explicit migration path. | Baseline tools documentation presents a downstream interface. Preservation is a conservative migration constraint, not a permanent endorsement of its implementation (U3). |

A shared Python CLI is not a consumer project's Python dependency environment.
Likewise, pinning pre-commit itself does not centrally own the consuming
repository's hook revisions or every environment those hooks create.

### Concrete consumers and success scenarios

Evidence below comes from the baseline at
`0cc738794384cf32f08ba616c049bf8f3fb7124c`, the current files where noted, and the
issue use cases. A documented interface is evidence of intended use, not proof
that all downstream consumers have been enumerated.

| Scenario and consumer | Proposed interface and platform | Required guarantee and success criterion | Evidence |
| --- | --- | --- | --- |
| S1: Module developer runs a formatter/linter; IDE runs its language server | Direct installed CLI in the published image, as the development user; Linux amd64/arm64 where the tool is supported | Command works without first installing tools at container startup. Shared tool version matches the release definition. IDE can use an executable path. | [Main usage guide](../README.md), [baseline inventory](tooling-status-quo.md), upstream decisions |
| S2: Lightweight CI checks a consuming repository | Release-selected pre-commit without Bazel/Container; Linux amd64, uv interface under evaluation | Resolves the centrally selected pre-commit version; passes arguments, cwd and exit status correctly. Consumer maintains its release reference and hook config, not another pre-commit pin. Launcher and bootstrap choice remain open; assess uv against the selected manager. | #189's use case; the reported shared-workflow command has not been independently audited here |
| S3: Existing Bazel consumer runs a shared CLI | `bazel run @score_devcontainer//tools:ruff -- ...` or existing pre-commit target; preserve platforms with existing artifacts | Uses that module release's tool definition; no new host Python prerequisite; preserves caller cwd and exit status. New internals must not silently break existing labels. | [Baseline tool guide](https://github.com/eclipse-score/devcontainer/blob/0cc738794384cf32f08ba616c049bf8f3fb7124c/tools/README.md), #190 |
| S4: Maintainer updates or adds a shared CLI | Repository-owned definition and environment selection; validate intended delivery paths | One maintained version decision, generated/resolved outputs may change. Selected paths and documentation agree automatically; a missing registration fails validation. | #190 and the duplication recorded in the baseline inventory |
| S5: Container maintainer builds and tests this repository | Separate repository development environment plus image build/test scripts; Linux amd64/arm64 | Build/test tooling is available without forcing it into the published consumer image. Existing image checks remain runnable. | [CI](../.github/workflows/ci.yaml), [architecture overview](README.md) |
| S6: Developer runs shared tools on Apple Silicon | Release-selected ruff and pre-commit in a native macOS ARM checkout, using the selected host delivery interface | Aim for the same declared versions as the release and preserved cwd/arguments/exit status. Document upstream platform gaps; no claim of current macOS validation. | User-confirmed target; native macOS ARM artifacts exist; end-to-end check still needed |

Representative image consumers already named in baseline CI are
`eclipse-score/score` and `eclipse-score/inc_someip_gateway`. CI invokes
[`scripts/test_consumer.sh`](../scripts/test_consumer.sh) on amd64, conditionally
for PRs. That is evidence of image consumers, not evidence that these repositories
use every public Bazel label or wrapper; their call sites have not been audited.

### run-tool: confirmed modes and container trust

The selected S-CORE container is assumed to contain the correct pinned tool
versions. Both modes may execute its installed tools directly. The runner does
not need to revalidate each executable or route container invocations through
Bazel. Correct installation and release validation establish that trust.

| Environment | Convenience: `run-tool <tool> ...` | Strict: `run-tool --strict <tool> ...` |
| --- | --- | --- |
| Selected S-CORE container | Use the installed tool directly | Use the installed tool directly; trust the container's pins |
| Host outside the container | May use the available PATH executable; otherwise use the pinned delivery path | Bypass arbitrary host tools and use the selected release's pinned delivery path |

Keep the existing interface and argument/cwd/exit behavior. If the container
command is missing, the existing pinned fallback may still be used; this does
not require packaging every container-only tool for Bazel.

The current [`tools/run-tool`](../tools/run-tool) container PATH branch is
consistent with this trust assumption. Its container behavior is **not** a
strict-mode defect merely because it does not verify a version at every call.
This clarification revises #190's earlier demand to reject unverified PATH tools
inside containers. A future issue update should reflect the agreed boundary;
this local record does not change the published issue.

### Clarifications confirmed on 2026-10-30

- **U1 resolved:** Multiple configs in one folder are acceptable. Normally
  describe direct dependencies only; no unified schema or hand-maintained
  transitive package inventory is required.
- **U2 resolved:** Matching tool versions are sufficient for this change.
- **U4 narrowed:** macOS on ARM is a desired host platform with reasonable
  per-tool limits. Validation coverage and exceptions remain to be established.

### Bazel: confirmed delivery boundary

**Decision:** Do not package complex tools for Bazel CLI delivery. The intended
scope is readily distributable self-contained executables, typically static
binaries. Python CLIs may also be exposed where a lightweight shared launcher
suffices, as in the current reference. If a tool needs bespoke runtime assembly,
OS dependency provisioning or a substantial packaging adapter, omit its Bazel
delivery path and document the supported alternatives.

This is the project's maintenance boundary, not a claim that Bazel or
`rules_multitool` technically cannot distribute other kinds of executable.
It does not require removing an existing working tool merely because its binary
uses the supported platform's runtime libraries. Bazel build/toolchain
integration remains a separate responsibility.

### Bazel: where the extra work comes from

The discussion raised an official Bazel baseline. The published decisions give
that a narrower meaning: DR-001 retains aspects for suitable build-aware analysis
but does not mandate Multitool delivery for independent CLIs. DR-003 requires
Bazel compatibility, not universal CLI packaging. Existing Bazel interfaces in
this repository and #190 are migration commitments to assess separately.

The build system and independent CLI distribution are separate responsibilities.
Existing public-interface changes need a consumer review and explicit migration
proposal. New complex tools are outside Bazel CLI delivery by default; they need
no elaborate adapter to satisfy these decisions.

The assessment below is based on code structure, not measured engineer-hours.

| Area | Observed additional work | Proposed treatment |
| --- | --- | --- |
| Existing native CLI delivery | [`MODULE.bazel`](../MODULE.bazel) registers 10 native lockfile hubs; [`tools/BUILD.bazel`](../tools/BUILD.bazel) separately lists 11 command aliases. The [shared validator](../tools/score_tools/catalog.py) checks that those lists match the catalog. Ordinary version changes still use the existing lockfile owner. | Low incremental burden while the current artifact format remains. Keep initially; derive registrations if justified. This repetition alone does not justify removing Bazel. |
| Python CLI delivery | [`python_tool.bzl`](../tools/python_tool.bzl) loads Starlark metadata and constructs a pinned uvx launcher; the [shell adapter](../tools/internal/run_python_tool.sh) handles Bazel-relative paths and caller cwd. Dedicated tests cover this boundary. Adding another Python tool already derives its target from the catalog. | A real adapter and test surface, but not a separate implementation per tool. Do not require the future primary config to remain Starlark just for this consumer; evaluate a generated adapter against actual downstream use. |
| Adopting a different tool manager | Conditional cost: if its definitions cannot directly supply existing Bazel targets, we need an export/generation step, metadata mapping and synchronization checks. A manager-driven execution path may also introduce a host bootstrap requirement. | Compare the concrete bridge for shortlisted candidates. Reject duplicate hand-maintained pins. Keep any bridge limited to simple supported tools. Do not build a substantial packaging subsystem to extend Bazel coverage; propose a migration if an existing public interface is affected. |
| Promising every tool through Bazel | Conditional cost: OS dependencies, services and complex runtime layouts would need additional packaging/adapters. The current baseline does not expose every container tool this way. | **Excluded by the confirmed scope.** Provide such tools through the container or another suitable delivery path; no Bazel packaging work is required. |
| Build-integrated tools and toolchains | These participate in action inputs, toolchain selection and cache correctness, beyond interactive CLI invocation. | Preserve this responsibility. Reassessing independent CLI distribution does not authorize removing build integration. |

Current evidence does **not** show that Bazel already causes disproportionate
maintenance for simple native tools. The largest possible extra cost is a new
cross-manager bridge, especially if we insist on extending it to every tool.
Limit any bridge to the confirmed simple-tool scope. Review users before
changing existing entrypoints; new complex tools do not enter that scope.

### Remaining decisions for review

| ID | Working recommendation | Remaining uncertainty and next evidence |
| --- | --- | --- |
| U5 — uv interface | Evaluate uv as a lightweight consumer/bootstrap option for #189, alongside direct use of the selected manager. | Compare initial setup, release selection, Linux/macOS ARM availability and additional maintained adapters. The no-Container/no-Bazel use case remains; uv-specific syntax is not yet adopted. |

U3 is resolved as a scope boundary: complex tools have no Bazel CLI delivery
requirement. The remaining implementation question is how cheaply to retain
simple existing interfaces under the selected manager. U5 remains open. No
manager is selected and no consumer interface is removed or published by this
record.

## 4. Existing behavior is evidence to investigate

The baseline inventory and reference remain useful migration evidence. They
should not silently determine the selection criteria for a new tool manager.

| Existing mechanism | Underlying need to investigate | Treatment until clarified |
| --- | --- | --- |
| APT version prefixes and distribution-managed packages | Compatibility, security updates, or simply the available packaging | Do not require a new manager to reproduce these exact policies by default |
| Per-package APT flags and temporary build dependencies | Runtime dependency needs versus image construction details | Keep as installation observations; require a user-facing reason before making them selection criteria |
| CodeQL pruning and extra setup | Required functionality, image size and startup behavior | Identify required commands/workflows; do not assume the current pruning script is the contract |
| Java installation paths and wrapper layout | Tools can find their runtime; consumers may rely on paths | Verify callers before promising exact paths |
| Separate native, Python, feature and OS metadata | Backend requirements versus avoidable duplication | Judge independent authoring decisions, not the count of generated or backend-specific files |
| Existing Bazel aliases and `run-tool` | Downstream invocation compatibility | Find consumers and classify interfaces before removing or freezing them |

Unknown does not mean unnecessary. A behavior may need to remain during migration
without becoming a permanent architectural requirement. Record such a constraint
with its consumer and eventual removal condition.

## 5. Research available for the eventual choice

These are candidates and research directions, not a ranked recommendation.
Capabilities need to be tested against the agreed scenarios, not every historical
edge case. Popularity is a maintenance/adoption signal, not proof of suitability.

| Candidate | Why it remains relevant | Main question for our scope |
| --- | --- | --- |
| [mise](https://mise.jdx.dev/dev-tools/backend_architecture) | Broad developer tool manager with multiple backends and Python CLI support | Can ordinary tool/version/environment maintenance use its conventions directly, with little repository-specific glue? |
| [aqua](https://aquaproj.github.io/docs/reference/registry-config/) | Declarative CLI artifact recipes and an existing registry | Does our required scope fit downloaded CLIs, or would Python/OS provisioning leave substantial parallel ownership? |
| [Nix](https://nix.dev/tutorials/first-steps/declarative-shell.html) | A package/environment model that also covers libraries and dependencies | Does adopting its ecosystem simplify our real requirements enough to justify the learning and integration cost? |
| [Pixi](https://pixi.prefix.dev/latest/reference/pixi_manifest/) | Conda/PyPI packages, environment composition and locks | Are the tools and versions we actually need available in that ecosystem? |
| [Devbox](https://www.jetify.com/docs/devbox/configuration) / [devenv](https://devenv.sh/packages/) | More convenient workflows on top of Nix | Can they reduce the team-facing cost without hiding integration work we still have to maintain? |
| [Ansible](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/apt_module.html) / [Hermit](https://cashapp.github.io/hermit/packaging/reference/) | Established provisioning modules or a portable tool packaging model | Would either remove more custom maintenance than it introduces for the selected delivery paths? |
| [Current local reference](tooling-reference-implementation.md) | Working comparison point using existing backend formats and shared metadata | Is the custom model necessary, and is it actually simpler than the alternatives? |

The prior comparison found no automatic universal representation of all existing
mechanisms. That is not a reason to reproduce them all in a new abstraction.
Likewise, an APT migration wrinkle is not by itself a reason to reject a candidate.

For the shortlist, retain dated upstream activity/adoption evidence, tool coverage,
normal update steps, supported platforms, integration needs and remaining custom
code. Avoid scoring candidates against requirements that are still open.

## 6. How this record reaches a decision

1. Evaluate U5 and candidate integration costs within the confirmed simple-tool
   Bazel boundary, version guarantee and macOS ARM direction in section 3. Record the remaining platform validation gaps.
2. Confirm or revise R1–R6 and the scope defaults. Promote reviewed assumptions
   to requirements; keep migration constraints distinct.
3. Reassess the existing research against that baseline. Run focused experiments
   only where they answer a remaining selection question. Do not rebuild the
   complete old setup for every candidate.
4. Record the selected approach, alternatives, reasons, consequences and any
   changes needed to upstream decisions here.
5. Derive a migration plan and small reviewable PRs from that decision. Keep
   #189 in the end-to-end validation, and justify any prerequisite work by what
   it enables rather than by its position in the old PR sequence.

The [target design](tooling-target-design.md),
[reference implementation](tooling-reference-implementation.md), and
[PR sequence](tooling-pr-sequence.md) document one explored approach. Their
technical validation remains evidence; their architecture and landing sequence
are conditional on this decision. The completed experiment does not settle the
requirements discussion.

## 7. Decision and consequences

**Requirements partially confirmed; architecture pending.** Multiple backend
configs in a common location are acceptable; normally describe direct
dependencies only. Matching declared tool versions suffice. macOS on ARM is a
host-support target with explicit per-tool exceptions and validation gaps.

Keep the container as default. Limit Bazel CLI delivery to simple self-contained
tools and lightweight Python adapters; complex tools are explicitly outside that
delivery path. Preserve existing simple public entrypoints during migration and
keep Bazel build integration separate. Evaluate uv rather than making it mandatory.

No manager, custom format, migration sequence or public-interface removal is
selected. This remains a local decision draft; nothing is published.
