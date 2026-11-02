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

# Version-maintenance workflow: mise, aqua and Nix

- **Date:** 2026-10-31.
- **Status:** Bounded implementation evidence; no architecture adopted.
- **Scope:** One Ruff version decision feeds native/container preparation, simple
  Bazel artifact metadata and ordinary uv/uvx dependency consumption.
- **Requirements:** [U5 and the decision record](tooling-decision-record.md).

The later [effort assessment](tooling-effort-conclusion.md) audits actual retained
installer duties and adds a managerless Python control. Its ownership conclusions
supersede the early qualitative preference below; historical update proofs remain
valid for their recorded scope.

## Criteria and integration assessment

The tables describe the variants actually probed for our requirements: existing
Ubuntu/Dev Container features, portable simple Bazel tools, native uv/uvx package
consumption, independently controlled tool versions and limited custom code.

- 🟢 **Direct fit:** standard capability or demonstrated small integration; no
  additional operating model for that criterion.
- 🟡 **Additional ownership:** explicit configuration policy, adapter, coordination
  or runtime assumption remains ours.
- 🔴 **Operating-model change:** introduces a different package/runtime model for
  this path, requiring an explicit architectural commitment. This does not mean
  unsupported or a failed test.

Colors are qualitative assessments against the stated criterion, not measured
engineering effort, universal product scores or counts to total into a winner.
All three passed the shared bounded functional checks. Every rating includes its
concrete reason; Nix's closure is a capability as well as a deployment commitment.

### Package model and maintenance

| Criterion | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Managed object | 🟢 Tool version with selectable installation backend | 🟢 Release artifact; Python package through separate uv backend | 🟢 Package including declared runtime dependencies |
| Authoritative Ruff selection | 🟢 Exact version in `mise.native.toml` | 🟢 Exact version in `aqua.yaml` | 🟡 Derivation selected from a locked Nixpkgs revision; version follows that package |
| Independent requested tool update | 🟢 Change version and refresh native lock | 🟢 Change version and refresh checksums | 🟡 Select a package snapshot containing that version; separate input or override where needed |
| Installation recipe ownership | 🟢 Upstream backend; aqua registry for the tested Ruff path | 🟢 Upstream aqua registry | 🟢 Upstream Nixpkgs package definition |
| Python CLI preparation | 🟢 Built-in backend invokes uv | 🟡 Separate standard uv provisioning step to coordinate | 🟢 Existing Python application package includes its selected runtime |
| Runtime library dependencies | 🟡 Chosen artifact must match the supplied system/runtime; OS setup remains separate | 🟡 Same artifact/system compatibility responsibility | 🟢 Package definitions retain required libraries/interpreter in their closure |
| Coupling of direct tool versions | 🟢 Individually selected versions | 🟢 Individually selected versions | 🟡 A package set selects multiple versions; separate locked inputs allow independent groups |
| Environment and lock conventions | 🟡 Maintain environment composition and native/Python lock-policy split | 🟡 Maintain native tags/checksum policy and Python selections; fixed image output uses `cp` | 🟡 Maintain package subsets and package-set ownership per independently controlled group |

### Delivery and repository integration

| Criterion | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Container provisioning into current Ubuntu/feature model | 🟡 Install at stable final paths; expose bins and retain venv/runtime references | 🟡 `aqua cp` for native binaries; uv prepares fixed Python venv | 🔴 Build bundle and transfer complete closure to `/nix/store`; introduces Nix's runtime layout into the Ubuntu image |
| Runtime files retained in container | 🟡 Tool install trees, venv and compatible interpreter; base Python sufficed in the probe | 🟡 Copied executable, venv and compatible interpreter; base Python sufficed in the probe | 🟡 Exact store paths including required libraries/interpreters; complete closure worked readonly |
| Runtime manager required for prepared container execution | 🟢 None | 🟢 None | 🟢 None; no daemon needed for the tested direct execution |
| Manager-native host invocation | 🟡 mise bootstrap; backend helpers during preparation | 🟡 aqua for native tools; uv for Python tools | 🔴 Native Nix/store bootstrap is a different host package model; exported uv consumption avoids this requirement |
| Our ordinary uv/uvx consumer prerequisites | 🟢 uv/uvx, release-selected package and normal Python build/runtime support; no mise | 🟢 Same; no aqua | 🟢 Same; no Nix |
| Resolver-visible release package | 🟡 Generate standard dependency metadata from authoritative tool selection | 🟡 Generate standard dependency metadata from authoritative tool selection | 🟡 Export selected version and generate the same standard dependency metadata |
| Existing simple Bazel Multitool delivery | 🟡 Derive URL/hash metadata; own archive/layout and registration mapping | 🟡 Same class of bounded adapter; actual Ruff Bazel run also exists | 🟡 Export version, obtain upstream portable binary hashes and apply asset/layout mapping; source hash alone is insufficient |
| New native-library/runtime packaging for Bazel | 🟢 Not required; complex tools excluded | 🟢 Not required; complex tools excluded | 🟢 Not required; Nix closure deployment is for the container, not a new Bazel packaging requirement |
| Native uvx execution without custom runner | 🟢 Demonstrated with release facade via `uvx --with ... ruff` | 🟢 Same | 🟢 Same |
| Binding all outputs to one release | 🟡 Refresh native lock, regenerate exports and validate drift | 🟡 Refresh checksums, regenerate exports and validate drift | 🟡 Resolve package selection, export versions/artifacts, generate package metadata and validate drift |

The red cells identify concrete Nix ecosystem adoption on the producer/container
or manager-native host path. They do not apply to its uv-only consumer, and do
not invalidate the successful Ubuntu closure handoff. Green runtime-dependency
ownership is the corresponding Nix advantage. No pass/fail ranking or proven
maintenance winner follows from these colors.

## Complexity assessment and proposed choice

**Historical proposal, superseded by the user’s implementation direction:** aqua plus uv. mise is a close
alternative, not a failed candidate. Nix is viable but introduces the largest
package/runtime commitment for the existing Ubuntu/feature architecture.
This is a qualitative architectural judgment, not an experimentally measured
cost difference or an adopted decision.

The criteria below assess **work this repository must own**, not the internal
complexity or feature count of each upstream product:

- **Low:** ordinary version/configuration changes or an existing standard
  operation; little new repository-specific policy.
- **Medium:** a maintained translation, coordination rule, release/drift check
  or runtime/path convention that we must design and keep correct.
- **High:** an additional package/runtime operating model spanning the producer
  and container lifecycle, beyond the confirmed direct-tool requirement.

The priority is preserving the current Ubuntu/features and uv consumer model
while minimizing additional repository conventions. Common required work
(Bazel export, standard Python dependency export and release binding) is treated
equally; green-cell counts are not added into a numerical score.

| Candidate | Independent version changes | Ubuntu/runtime integration | Simple Bazel metadata adapter | uv dependency package and release binding | Extra configuration/operating conventions | Overall expectation for this scope |
| --- | --- | --- | --- | --- | --- | --- |
| **aqua + uv** | **Low:** edit direct package version, regenerate checksums | **Medium:** explicit binary copying and fixed Python environment/interpreter paths | **Medium:** retain archive/layout mapping and generated metadata checks | **Medium:** derive dependency metadata, build/distribute release, validate drift | **Low–medium:** registry/checksum/tag policy plus explicit standard uv provisioning | **Low–medium; preferred fit.** Required glue remains, but the narrowly defined backends match the two existing tool categories. |
| **mise** | **Low:** edit direct tool version, regenerate native lock | **Medium:** stable install/venv paths and executable exposure | **Medium:** same class of archive/layout and registration adapter | **Medium:** same dependency exporter and release binding; the common frontend does not remove this | **Medium in the tested design:** backend/profile composition and native/Python lock split | **Low–medium; close alternative.** Useful upstream orchestration, with additional profile/lock policy in the demonstrated solution. |
| **Nix** | **Medium:** select suitable locked package snapshot/input; independent versions may need separate groups or overrides | **High relative to current architecture:** preserve and transfer the complete store closure in the Ubuntu image | **Medium:** version export plus upstream binary hash/layout acquisition; no complex Bazel packaging | **Medium:** same standard package mechanism after exporting selected version | **High relative to scope:** own package-set grouping and store lifecycle; native host Nix adds bootstrap, while uv-only users avoid it | **Higher producer/image integration commitment.** Existing package/runtime ownership is valuable if explicitly desired, but is broader than the current request. |

### Why prefer aqua plus uv here

1. Native release artifacts and Python distributions are the two concrete
   categories we have to deliver. Multiple backend configurations are accepted;
   uv is already a required consumer interface. Their separation is therefore
   not itself a problem to solve.
2. The observed aqua path uses registry-backed copying and ordinary uv package/
   environment operations. It needs no new combined profile/lock convention for
   this selection. Its registry/checksum policy and Python preparation still
   require explicit maintenance.
3. The demonstrated mise design adds useful shared install/bin discovery, but
   does not remove the required Python release export, Bazel bridge or runtime
   paths. For this scope, I would prefer the explicit two-backend workflow over
   the additional combined-manager conventions. This is the deciding preference,
   not a proven large reduction in code or engineering hours.
4. Nix's package/runtime closure management genuinely works and owns dependencies
   upstream. Here, OS/features remain separate and complete runtime ownership is
   not a confirmed need; adopting that additional model is not the simplest
   route to the requested tool/version delivery.

The difference between aqua and mise is **small and preference-sensitive**.
If shared native/Python setup, broader backend orchestration or team familiarity
with mise is worth its conventions, mise can be an equally reasonable choice.
The tested configuration is not proof that mise inherently requires this exact
lock/profile split in every design. Ecosystem adoption is an additional factor,
not measured maintenance effort; it does not turn this close comparison into an
objective winner. Nix becomes more attractive if comprehensive runtime/package
ownership becomes an explicit requirement.

Official [aqua container provisioning](https://aquaproj.github.io/docs/guides/build-container-image/)
and [mise environment configuration](https://mise.jdx.dev/configuration/environments.html)
document the standard operations; the tradeoff and complexity levels above are
our judgment based on the local before/after probes and confirmed requirements.

**Current direction:** the user wants all three implemented further equally.
The [shared reference milestone](../experiments/tool-manager-comparison/reference-milestone.md)
replaces the earlier single-candidate recommendation as the active plan. Retain
these qualitative estimates and revise them against the maintained reference
implementations. No candidate is adopted or authorized for publication.

The [common reference implementation](tooling-reference-milestone.md) records the
maintained delivery paths and their ownership boundaries beyond these probes.
The subsequent [repository integration](tooling-repository-milestone.md) extends
all three into actual root consumers and built tooling images; the early cost
estimates above remain qualitative hypotheses rather than measured migration effort.

## What is now comparable

All three candidates have completed the same focused version-maintenance path.
The [round-three protocol](../experiments/tool-manager-comparison/round3-protocol.md)
requires an actual before/after version change, a normal consumer package
requirement, resolver-visible metadata, a consumer lock and real uv/uvx execution.
This closes a gap that the earlier requirements-file probes did not cover.

| Observable before → after | mise | aqua | Nix |
| --- | --- | --- | --- |
| Selected Ruff version | 0.11.13 → 0.11.12 | 0.11.13 → 0.11.12 | 0.17.2 → 0.14.6 |
| Actual native Ruff execution | Both versions observed | Both versions observed | Both package bundles built and versions observed |
| Generated Bazel version/artifact selection | Matches both selections | Matches both selections | Matches both selections; upstream binary digests fetched separately |
| Standard package dependency metadata | Generated exact Ruff dependency for both releases | Same | Same |
| Consumer uv dependency, lock and real Ruff invocation | Both versions observed | Both versions observed | Both versions observed |
| Actual uvx Ruff invocation, without custom runner | Both versions observed | Both versions observed | Both versions observed |

Different supported historical versions are update fixtures, not proposed
production downgrades. A facade package release is a separate identifier from
the Ruff version. The consumer selects our release/extra; it never authors a
second Ruff pin. Exact dependency pins in generated lockfiles are resolver
outputs, not extra maintained version decisions.

This does not claim three full migrations. Bazel metadata was generated and
inspected in this round, not executed again through Bazel. The earlier aqua
Bazel run remains narrower existing integration evidence. Prepared non-root
Ubuntu runtime handoff was already proved in round two; the new native selections
were exercised without rebuilding full production images. macOS ARM execution
and complete tool-catalog coverage remain outside these probes.

## The concrete authoring changes

### mise

Maintained input, `mise.native.toml`:

```diff
 [tools]
-"aqua:astral-sh/ruff" = "0.11.13"
+"aqua:astral-sh/ruff" = "0.11.12"
```

The normal mise update refreshes the generated native lock. The existing bounded
Bazel exporter reads the resolved artifact/version data; the package exporter
reads this authoritative version and writes ordinary Python metadata. Native
installation, Bazel metadata and Python metadata share one Ruff owner. The
separate Python/lock-policy configuration established earlier is not another
Ruff pin.

### aqua

Maintained input, `aqua.yaml`:

```diff
 packages:
-  - name: astral-sh/ruff@0.11.13
+  - name: astral-sh/ruff@0.11.12
     tags: [container, repository, lint]
```

Normal checksum refresh updates generated artifact hashes. `aqua cp` uses that
selection for direct installed executables. The bounded existing Bazel exporter
and static Python metadata generator derive the same Ruff version. The ordinary
Python requirements used for other tools do not acquire an independently edited
Ruff pin.

### Nix

Maintained input, `flake.nix`, selecting between already locked package inputs:

```diff
-          inherit (pkgs) ruff pre-commit;
+          inherit (pkgs) pre-commit;
+          inherit (alternatePkgs) ruff;
```

The inputs contain Ruff 0.17.2 and 0.14.6 respectively. Their revisions are locked;
`pkg.version` supplies the derived version string. No separate hand-authored
Ruff number or new package recipe is added. Native package construction uses the
selected derivation; `nix eval` exports the version for both downstream formats.

For portable Bazel metadata the probe additionally obtains upstream Ruff binary
asset digests and applies the same class of archive/platform mapping as the
peers. Nix's source hash is not mistaken for a release-binary hash. The consumer
package metadata is generated from the exported version, not from another pin.
Finding a package snapshot containing an arbitrary desired version remains
part of Nix maintenance; two already available snapshots make this particular
change small, not evidence that every desired version is equally easy to select.

## The uv mechanism is shared, not a manager feature

All three use the same ordinary package model: a facade/metapackage with a
resolver-visible extra. The generated metadata has the following shape:

```toml
[project]
name = "score-tools-probe"
version = "0.1.0"

[project.optional-dependencies]
ruff = ["ruff==0.11.13"]
```

This snippet is illustrative: names/extra/release numbers are not an adopted
API, and the Ruff field is generated from the authoritative choice above.
The real fixtures use standard setuptools metadata, no application module and
no entrypoint. Ruff's own distribution supplies its executable. The ordinary
consumer build does not invoke mise, aqua, Nix or a custom package installer.

mise and Nix used two independent local Git releases; aqua built two local
wheels. Both are ordinary package-source mechanisms. Their source differences
are not scored as candidate capabilities. The consumer project adds our
release-selected package/extra, locks/syncs, then runs actual Ruff through uv.
The evidence inspects both the lockfile and package `Requires-Dist`, rather
than inferring resolution from a command alone. aqua inspected the built wheel
metadata; mise and Nix also inspected installed metadata.

The cleaner native uvx invocation observed for all candidates is conceptually:

```sh
uvx --with 'score-tools-probe[ruff] @ SELECTED_RELEASE_SOURCE' ruff --version
```

`SELECTED_RELEASE_SOURCE` stands for the local Git/wheel URI used in the probe;
this is not a published command/API. The extra constrains Ruff in uvx's normal
resolver. No Ruff version is supplied by the consumer and no custom runner
intercepts execution. The project workflow likewise selects the package release
and uses `uv run ruff` (the mise/aqua probes additionally used `--locked`).

`uvx --from 'FACADE[ruff] @ SOURCE' ruff` also worked, but uv 0.11.2 warned that
the executable came from a dependency rather than the facade itself. The aqua
agent tested `--with` and shared it; both peers tested it for both of their
releases too. That form resolves the requested version without that warning.
No wrapper executable or warning suppression was introduced.

A `score-tool` convenience command remains possible; it is not necessary for
this dependency path and would not own the version decision.

## Comparable complexity ledger

| Ongoing responsibility | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Authoritative version selection | Direct version in native TOML | Direct version in native YAML | Derivation selected from locked package set(s) |
| Native download/package recipes | Upstream mise backend/registry | Upstream aqua registry | Upstream Nixpkgs package recipe |
| Native generated resolution data | mise native artifact lock | aqua generated checksums | Nix input lock and selected derivations/closure |
| Package dependency export required by U5 | Small producer-side standard metadata generator | Same class of generator | Same class of generator after version export |
| Retained simple Bazel export | Version/artifact mapping and archive-layout integration | Same class of integration | Version export plus upstream binary digest/layout integration |
| Container lifecycle | Stable install/venv paths, executable exposure and runtime availability | Same, with explicit aqua copying and uv venv preparation | Preserve/expose complete selected runtime closure |
| Host consumer of facade package | uv/uvx, selected release artifact, normal Python build/runtime support | Same | Same; no consumer Nix installation required |
| Release/CI integration | Refresh lock, regenerate both exports, verify drift, bind outputs to release | Refresh checksums, regenerate both exports, verify drift, bind outputs to release | Resolve/build package selection, export version, generate both exports, verify drift, bind outputs to release |

The permanent package generator and release wiring are real additional work for
all three; mise's common frontend does not remove them. They are separate from
temporary test Git repositories, fixture wheels, test tags, consumer projects,
probe scripts and evidence copies. Those disposable files are not production
architecture. Prototype line counts, elapsed time and the number of files are
not maintenance measurements.

No generic catalog converter was built. All three Ruff examples know applicable
backend/PyPI identity and archive/platform layout. A broader implementation must
state how those mappings are owned and handle tools without Python distributions
without forcing them onto uv or Bazel.

## What the comparison supports

**Yes: the same narrow workflow is now comparable across all three.** Their
normal dependency/uvx routes are actual evidence, not hypothetical metadata or
requirements-only execution. It is possible to compare the responsibilities
above; it is not yet possible to quantify full migration effort or long-term
maintenance hours from these probes.

The probes do not establish a measured complexity win for mise over aqua. The
qualitative assessment above proposes aqua plus uv for the stated scope. Both need
one maintained native version decision, backend-generated hashes, a bounded
Bazel adapter and a standard package metadata export. Their real distinction is
whether common mise orchestration/profile conventions or explicit aqua/uv
backend steps are the preferred maintainer workflow.

Nix reaches the same result. It additionally commits the producer/container
workflow to package-set selection and store-closure lifecycle; its uv consumer
can nevertheless be as small as the others. That is an identifiable operational
tradeoff, not a defect inferred from an unattempted test or a failed ELF copy.

This investigation answers the open package-consumption question. Another
general capability survey or another round of equivalent Ruff checks would not
settle the maintainer-workflow preference. Public package naming/extras/source,
release automation and whole-catalog export rules remain implementation choices;
aqua plus uv is proposed above, while no manager or production API is adopted here.

## Local evidence

Each sibling worktree retains `experiments/tool-manager-CANDIDATE/round3/`:

- mise: `eval/tool-manager-mise`, local Git release fixtures, authoring/generated
  diffs, consumer locks/metadata, commands/results and its report.
- aqua: `eval/tool-manager-aqua`, two facade wheels, authoring/generated diffs,
  consumer locks/metadata, commands/results and its report.
- Nix: `eval/tool-manager-nix`, both package-set selections/native bundles,
  version/artifact exports, local Git releases, consumer metadata and results.

The agents cross-read the final reports, authoring diffs, generators and consumer
evidence and directly exchanged corrections. The parent synthesis was also
reviewed; distinctions between wheel versus installed metadata and exact uv
flags were retained rather than presented as identical observations.

These are uncommitted local artifacts. Preserve relevant evidence before removing
worktrees. The producers and consumers are isolated fixtures; no package was
published and no production install path was replaced by this experiment.
