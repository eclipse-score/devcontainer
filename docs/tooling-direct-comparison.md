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

# Direct comparison of tool provisioning approaches

## Decision after the four-option comparison

**Decision recorded 2026-11-02: consolidate own provisioning for the confirmed
scope. Upstream implementation remains pending.**
The three-manager comparison below is historical; this assessment includes
[the maintained own implementation](tooling-own-provisioning.md) and its
[compact source-bound evidence](../experiments/tool-manager-comparison/own-evidence/README.md).

The previous control was smaller than the manager implementations. That is no
longer a reason to leave its core complexity unassessed: the own variant now
passes the maintained release/update, repository lifecycle, fresh complete
amd64 feature-image and ARM64 prepared-tool boundaries. Codespell is an extra
selection in the peer inventory, not present in the own baseline. Different
initial versions and selections are disclosed; this is common-contract parity,
not four byte-identical installations or an exhaustive production review.

### Why we choose own provisioning

Existing portable URL/hash/archive-layout definitions must remain for supported
simple Bazel tools. The own implementation uses those definitions for native
provisioning too. It therefore avoids manager-owner-to-portable-Bazel translation
and adds no manager configuration/bootstrap/registry or Nix store model.
It has one shared download/extraction engine for container and host, not the old
engine plus a new parallel one. Ordinary Python release metadata comes from the
same owners and works through uv/uvx without a launcher.

This is not zero custom infrastructure. The provisioner adds content-keyed
prepared packages, completion markers, locking and direct command links.
It owns download/checksum/extraction/layout handling and uv environment setup.
Interrupted Python preparation requires a fresh data directory; installations
are trusted, not rehashed before every invocation. Use a fresh prefix for
migration; arbitrary old installations are not adopted. Those are real limits,
but not reasons to introduce unrequested uninstall/rollback machinery.

External backends/registries can take over release-asset discovery and recipes.
mise has fewer local exceptions than Aqua in the inventory evaluated. That is
the strongest case for adopting either; #189's ordinary dependency wheel and
fast direct calls do not require them. Nix additionally handles runtime closures
and profiles, which is a broader operating commitment alongside retained Ubuntu
providers. It needs a deliberate requirement for those capabilities.

### Shared base, final complexity and migration delta

The existing setup must be learned by most contributors too. Existing custom
code is not simpler merely because two people know it. Compare the complete
post-cleanup system separately from the one-time work of changing today's setup.

All variants still own tool/version selections, Ubuntu providers, public
interfaces, ordinary Python releases and agreement/drift checks. Their
mechanisms can be replaced; keeping existing own code gives no familiarity
bonus. Migration means both additions and deletions, not just added layers.

More points mean less ongoing SCORE complexity: 🟥 1, 🟧 2, 🟨 3, 🟦 4, 🟩 5.
These are ordinal review judgments, not measured effort or a total score.

| Ongoing maintenance question | Own | mise | Aqua + uv | Nix |
| --- | --- | --- | --- | --- |
| How little download/unpacking code stays ours? | 🟨 **3/5** | 🟦 **4/5** | 🟦 **4/5** | 🟦 **4/5** |
| How easy is an isolated version change? | 🟦 **4/5** | 🟦 **4/5** | 🟦 **4/5** | 🟧 **2/5** |
| How few installation exceptions are needed for current tools? | 🟦 **4/5** | 🟦 **4/5** | 🟨 **3/5** | 🟨 **3/5** |
| How easy is keeping Bazel downloads in sync? | 🟩 **5/5** | 🟨 **3/5** | 🟨 **3/5** | 🟧 **2/5** |
| How simple is the delivery machinery? | 🟦 **4/5** | 🟨 **3/5** | 🟨 **3/5** | 🟥 **1/5** |

The old learning row mixed one-time introduction with ongoing complexity and
is removed. No onboarding measurements exist. The own isolated-update rating
is corrected to 4: all three exercised one version decision plus normal
refresh/check. A 3-versus-4 difference was not sufficiently supported.

Own's final complexity includes a shared download/checksum/extraction engine,
prepared-tree state, completion markers, locks, uv environments and links.
It directly reuses Bazel artifact owners. mise/Aqua delegate installation but
retain bootstrap/provisioning and portable artifact adapters; mise covers
Starpls/APM with existing backends, whereas Aqua needs local recipes/layout
handling. Nix has custom OpenCode packaging and store/closure delivery; an
isolated version selection needed a separate known package input. These are
concrete duties, not differences inferred from code age or line counts.

| Migration option | Add/change | Remove/retain |
| --- | --- | --- |
| Own | Shared host/container provisioning, prepared output, dependency releases, generated registration | Remove duplicate container engine; retain one generic engine and portable owners |
| mise | Manager owners/bootstrap, portable/Python adapters, migrate callers/automation | Remove old install engine; retain providers and SCORE compatibility/release glue |
| Aqua + uv | Registry/uv integration, missing recipes, adapters, migrate callers/automation | Remove old install engine; retain providers and SCORE compatibility/release glue |
| Nix | Inputs/derivations, closure production/transfer/activation, adapters, migrate callers/automation | Replace old installer/runtime composition; retain providers and SCORE compatibility/release glue |

The own decision is based on fewer artifact translations and one
shared engine, not on assuming the current setup is familiar. Its retained
engine is still a maintenance cost. mise is the alternative if delegated
recipe/engine ownership matters more; Aqua has more observed local recipe
exceptions without a demonstrated compensating simplification. Nix supplies
broader runtime capabilities at a broader operating commitment. No total score
or universally simplest solution follows. Unrequested host uninstall/repair
capabilities are excluded from required parity.

### Review performed and remaining limits

The [focused parent review](../experiments/tool-manager-comparison/own-review.json)
read the maintained installer, package generator/checker, registration
changes and regression coverage. It independently reran all 45 unit tests,
inventory/registration checking, and the evidence verifier (99 archive records,
48 current-source hashes and integration bindings). It inspected both real
wheel metadata records: facade A 0.8.0 selects Ruff 0.11.13, B 0.8.1 selects
0.14.6. The parent also reran the amd64 prepared-runtime suite as uid 1000,
network disabled, with read-only root/prefix: 16 direct/strict pairs, two behavior
cases and three language-server exchanges passed, with no intercepted manager
or launch-time Bazel calls. The root review is focused and does not imply a
second full-image build or exhaustive platform/security audit.

The worker's fresh no-cache amd64 build passed 79 unchanged feature assertions
on original URLs, with cache-only output rather than a separately loaded image.
ARM64 prepared execution under QEMU passed. A full ARM64 image attempt reached
16 assertions before its 30-minute cap; the 45-minute retry failed earlier on
a connection reset downloading the retained Bazel provider. A targeted real
ARM Bazel download/execution then passed, including offline cached execution.
These are separate records; the full ARM image remains open. macOS/native ARM
hardware, public identity/hosting, production rollout and final upstream review
are also open, including for a recommendation that favors the own variant.

Implementation direction: use the own variant as the target, resolve final
platform/release gates and split it into reviewable PRs. Prefer Aqua/mise-like
patterns wherever that adds no implementation or maintenance effort, such as
clear declarative definitions and separation from installation. Resemblance is
a preference for equally simple choices, not a reason to add formats, adapters
or features. Other variants remain evaluation evidence rather than parallel
production implementations.

## Historical three-manager comparison

- **Date:** 2026-10-31.
- **Status:** Follow-up evidence after mutual review; architecture not adopted.
- **Subsequent clarification:** U5 requires native uv/uvx execution and normal package-dependency
  consumption; an optional runner is allowed. See the decision record for the current contract; the experiments
  predate this clarification. The later
  [version-maintenance comparison](tooling-version-workflow-comparison.md)
  implements and verifies the bounded package/dependency/uvx route for all three.
- **Requirements:** [Decision record](tooling-decision-record.md).

**Operational follow-up:** [recovery, integrity and selection changes](tooling-operations-comparison.md)
compares three additional executed criteria, including the managerless control.

## Why the first comparison was insufficient

The first three probes shared requirements, but their authors chose different
implementation paths and verification depths. Comparing their reports afterward
risked rewarding how far an agent happened to get rather than the suitability
of its candidate. In particular, a single manager interface did not establish
lower maintenance, and testing only a copied Nix executable did not evaluate
its supported runtime deployment.

The agents therefore read each other's reports, configurations and adapters,
exchanged technical questions directly, and agreed three outcome-based follow-up
checks. Their second-round results were then exchanged for review. The initial
mise preference remains a hypothesis, not a decision carried forward by default.

## Common protocol and results

The [shared protocol](../experiments/tool-manager-comparison/protocol.md) defines
allowed implementations and evidence classifications. Multiple configurations,
generated locks/exports, standard uv companions and complete runtime closures
are allowed. Matching tool versions suffice; no candidate must reproduce every
old image workaround or package complex tools for Bazel.

The parent built and verified one Ubuntu 24.04 runtime base with Git, Python
3.12.3 and uid/gid 12345. It has none of Ruff, pre-commit, uv, mise, aqua or Nix.
All runtime checks use this exact local image ID:

```text
sha256:1b1ebf493ffb1a5a3a4d3c4c2a822cfe0da563d7028159078b0a02a12122a28d
```

| Shared outcome | mise | aqua + uv | Nix, with generated uv requirements for host use |
| --- | --- | --- | --- |
| C1: one direct tool changes, the other retains its version | Ruff 0.11.13 → 0.11.12; pre-commit stays 4.7.0 | Ruff 0.11.13 → 0.11.12; pre-commit stays 4.7.0 | pre-commit 4.7.0 → 4.3.0 from a second locked package set; Ruff stays 0.17.2 |
| C2: selected tools run outside the config checkout despite conflicting PATH/project configuration | Passed through explicit release-config selection plus caller-cwd adapter | Passed through absolute aqua config and requirements paths with explicit uv options | Passed through exported standard requirements and uv, without host Nix |
| C2: actual relative-file/argument/cwd/exit behavior | Ruff F401/exit 1; local pre-commit hook checks caller cwd/arguments | Same observable outcomes | Same observable outcomes |
| C3: both prepared tools execute directly, non-root, network disabled | Passed with retained install/venv paths and base Python | Passed with copied native executable and fixed venv against base Python | Passed with complete runtime closure at `/nix/store` |
| C1 update reaches prepared Ubuntu runtime | Targeted version check of changed Ruff and unchanged pre-commit passed | Targeted version check of changed Ruff and unchanged pre-commit passed | Full runtime check uses the changed pre-commit selection |

The older versions are intentional update fixtures, not proposed production
downgrades. C1 uses each ecosystem's normal way to select another published
version; identical historical versions or unchanged transitive dependencies are
not requirements. Full baseline fixture checks and narrower post-update version
checks are separate evidence, not a claim that a complete deployment pipeline
has been implemented.

Actual host execution was Linux x86_64. The Nix host route above is a real uv
consumer of generated metadata, not Docker counted as a native host invocation.
Native `nix run` on this host remains untested because Nix is not installed.

All candidates pass the agreed small outcomes. This is functional evidence,
not a numerical ranking, complete tool-coverage audit or proof of equal behavior
for arbitrary tool dependencies and downstream hooks.

## What maintainers would actually own

| Responsibility | mise approach | aqua + uv approach | Nix approach |
| --- | --- | --- | --- |
| Select/update direct versions | Native TOML entries; generated URL/hash lock for native tools | Native YAML versions and pinned registry; Python requirements | Locked package-set input supplies package versions; independent groups can use another input |
| Keep Python version-only | Separate Python configuration without a graph lock | Ordinary requirements file | Select an existing Nixpkgs application; uv consumers receive generated requirements |
| Compose environments | Config environments/overlays; preserve native-versus-Python lock convention | Native tags for selection; requirements selections for Python | Reusable explicit package subsets |
| Prepare image tools | Install at stable final paths; retain venv/interpreter references and expose bins | `aqua cp` for native tools, uv prepares a fixed venv | Build selected bundle and preserve its runtime closure at supported absolute paths |
| Invoke selected host release | Manager bootstrap and explicit config selection; tested call needs cwd restore | Native/backend invocations can keep caller cwd with explicit config paths | Native Nix host bootstrap, or exported release metadata plus uv |
| Preserve simple portable Bazel tools | Derived metadata plus archive-layout mapping and registration integration | Same class of adapter; first round actually ran generated Ruff target | Version export plus additional upstream binary asset/hash/layout mapping |
| Confirmed native uv/uvx and dependency interface | Derive standard package dependencies from selected definitions | Package standard tool dependencies from authoritative definitions | Derive standard package dependencies from selected derivations |

These are the concrete responsibilities identified by the probes. They are not
measured engineer-hours. File counts, manager names, prototype line counts,
cache sizes and first-install timing are not substitutes for those costs.

### Independent updates

mise and aqua demonstrated ordinary version-string changes with generated
artifact data refreshed. Their Python companion selection remains unaffected.
For Nix, the first single package-set input coupled ordinary package refreshes;
the follow-up instead uses a second published input for pre-commit. This works
without a custom package recipe or handwritten dependency tree. The extra work
is identifying and pinning an appropriate package snapshot and deciding which
group owns it. It is not technically impossible, nor always just a version-string
edit. The Nix probe's second input is revision
`b6018f87da91d19d0ab4cf979885689b469cdd41`; Ruff retains the original input
`1c89083e451e891152365b799595cf7790a43325`.

### Selected host calls

The mise probe's explicit `-C RELEASE` selection changes cwd. Its small adapter
selects that configuration and then restores the consumer cwd before executing
the real tool. That tested path works; it is not proof that every possible mise
invocation requires such an adapter.

The aqua probe can select `aqua -c ABS_CONFIG` while retaining cwd. Its Python
companion uses uv with `--no-project --no-config` and absolute requirements.
The Nix export uses the same standard uv approach. Conflicting consumer settings
and same-name PATH commands were tested, rather than merely assumed harmless.

None of these experiment wrappers is the final public strict runner. A production
entrypoint still needs deliberate release/config selection and registered tool
handling. `run-tool` continues to trust container-installed versions in both
modes; only the host pinned path must bypass arbitrary host tool selection.

### Prepared runtime and dependencies

mise and aqua both demonstrated direct pre-commit execution against the common
system Python, with the venv created or retained at a valid fixed path. Neither
required a newly maintained interpreter pin for this selection. Paths, access
permissions and Python availability still matter for both approaches.

Nix carries its selected interpreter/libraries in the closure. The complete
closure worked readonly in the same Ubuntu base without invoking Nix at runtime.
An initial extraction attempt failed on early restoration of readonly directory
permissions; a corrected tar extraction completed the handoff. This is real
provisioning work to own, not evidence of a package incompatibility. The previous
single-ELF copy failure should not be used to reject Nix deployment.

No result requires distributing these closures or complex runtimes through Bazel.

## What changed through direct exchange

- The agents withdrew the unsupported inference that mise's single frontend
  necessarily means lower maintenance. It uses uv and aqua recipes itself.
  Upstream dependency ordering/bin discovery are useful features; a two-backend
  aqua/uv workflow is also valid under the confirmed requirements.
- mise's split native/Python lock configuration is a workable native solution,
  but remains a convention to maintain, not a free advantage over two configs.
- aqua's fixed `cp` output is the correct image-selection mechanism. Tags on
  lazy installation alone must not be confused with fixed tool availability.
- Nix's native multi-input selection closes the independent-update evidence gap
  without inventing recipes. Complete closure deployment closes the Ubuntu/
  non-root gap rather than repeating the unfair standalone-ELF comparison.
- The parent found that separate baseline runtime and host-update successes did
  not by themselves prove post-update runtime propagation. mise and aqua added
  targeted checks of the updated installed output, without repeating the full
  fixture suite or claiming a production rollout.
- All three can support a uv-only consumer through native or derived metadata.
  Giving only mise permission to replace that interface with its own manager
  would bias the comparison. U5 now requires native uv/uvx and package-dependency consumption consistently;
  optional runners are allowed. Requirements-only probes are partial evidence.

## What remains a real distinction

**mise** supplies common dependency ordering, version editing and bin discovery.
Its profile/lock conventions, explicit release invocation and existing delivery
exports still need repository integration. The probe establishes that those
pieces can be small; it does not prove a net maintenance win over aqua plus uv.

**aqua plus uv** provides a narrow native-artifact backend and a standard Python
backend. It does not unify their lifecycle, but the required glue proved small
for this selection, including cwd-preserving invocation and direct provisioning.
The native registry/checksum lifecycle and Python environment preparation remain
explicit responsibilities.

**Nix** provides existing package/runtime ownership and reusable environments.
It can deliver the required results, including prepared Ubuntu execution and
independent updates. Its package-set selection, store handoff and native host
bootstrap are different operational commitments. A uv-only export can avoid
native Nix bootstrap for that consumer, but portable Bazel artifacts still need
a separate binary-metadata bridge. Those tradeoffs matter; inability to copy one
executable or the absence of a first-round test does not decide suitability.

The shared checks therefore do not establish a unique winner. The initial mise
preference is not restored merely because all checks passed. An eventual choice
must state which maintainer/consumer workflow is preferred and which of these
concrete responsibilities the team accepts. In particular, compare a manager-
producer-side manager integration consistently while retaining the confirmed
native uv/uvx dependency interface. The bounded package route is now verified in the later comparison; production
release integration remains. An optional runner does not replace dependency metadata.

## Evidence locations and limits

The same three local worktrees remain available. Each experiment now contains
`peer-review.md`, `comparison-round2.md` and reproduction/evidence files:

| Sibling worktree / branch | Experiment directory |
| --- | --- |
| `score_devcontainer-eval-mise` / `eval/tool-manager-mise` | `experiments/tool-manager-mise/` |
| `score_devcontainer-eval-aqua` / `eval/tool-manager-aqua` | `experiments/tool-manager-aqua/` |
| `score_devcontainer-eval-nix` / `eval/tool-manager-nix` | `experiments/tool-manager-nix/` |

These are uncommitted local artifacts. Preserve relevant evidence before removing
worktrees. The primary decision record and this summary retain the conclusions
without relying exclusively on those paths.

Actual macOS ARM execution remains a common gap; artifact resolution/evaluation
is not execution. No production-wide migration, complete image build, complete
Bazel converter, exact public Git-release launcher or ten-year archive guarantee
was delivered by these probes. The first-round aqua Ruff Bazel run, mise metadata
equivalence and Nix version export retain their different evidence scopes; they
are not converted into capability rankings here. No additional broad tests are
needed merely to equalize test counts.
