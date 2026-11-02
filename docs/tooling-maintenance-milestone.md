<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Maintaining the three variants: adding real tools

Milestone 4 compares a maintainer operation after the
[full-image milestone](tooling-production-milestone.md): add a tool through the
existing native, Bazel, Python-package and prepared-runtime paths. The
[shared contract](../experiments/tool-manager-comparison/maintenance-milestone.md)
keeps the change request and acceptance criteria equal. All work stays local;
no manager is adopted.

The subsequent [effort conclusion](tooling-effort-conclusion.md) compares retained
installer duties and the managerless baseline; onboarding success alone is not a
reason to adopt a manager.

## The concrete change

The larger `published` selection gains **starpls** and **codespell**. starpls
already exists in the repository, but its delivery previously remained on the
legacy path. codespell represents a new Python CLI, not a proposed new lint
policy. Both remain outside the smaller `repository` selection.

Native configuration owns each version. Existing `//tools:starpls` is preserved;
the shared Python catalog exposes `//tools:codespell`. A normal generated
codespell package extra must work with uv project dependencies and uvx without
a second consumer-authored tool pin. starpls has no corresponding Python extra.
The existing feature installer must recognize both prepared tools and skip
their old installation paths.

## What native package availability actually changes

The observations below apply to these locked inputs and this tool, rather than
to every tool supported by a manager.

| Concrete operation | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Find starpls in the already used source | Standard aqua registry entry is absent | Standard registry `v4.579.0` reports unknown package | Existing locked `pkgs.starpls` is available |
| Native route used | Built-in GitHub release backend | Local GitHub release registry recipe | Existing Nixpkgs derivation |
| Native starpls version | 0.1.22 | 0.1.22 | 0.1.22 |
| codespell version source | Exact PyPI selection, 2.4.1 | Exact uv dependency-group selection, 2.4.1 | Locked `pkgs.codespell`, 2.4.3 |
| Additional upstream recipe we own for starpls | No custom installation recipe; bounded identity/export mapping remains | Small local release-asset/platform recipe plus export mapping | No new package recipe; portable Bazel metadata remains a separate export |

Nix's existing package availability is useful here. mise's generic release
backend also handles the missing registry entry. aqua requires owning a small
recipe for that gap. None of those observations alone settles the complete
architecture decision.

## Separate repeated maintenance from implementation gaps

Each candidate records a ledger of authored policy, permanent adapter changes,
generated outputs and executed acceptance. The ledger distinguishes a normal
operation for each new tool from a one-time limitation exposed in the prototype.
For example, a new tool's command/package identity is real metadata work; a
hardcoded list that accidentally prevents adding any tool is an implementation
gap to fix and share. Neither is measured by counting lines or experiment files.

All three implementations completed the shared checkpoint. The recorded
[maintenance ledgers and behavior proofs](../experiments/tool-manager-comparison/maintenance-evidence/)
retain the actual versions, command paths, network conditions and limitations.

| Executed criterion | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Fresh native selection and prepared payload expose both tools | 🟢 | 🟢 | 🟢 |
| Real starpls initialize/shutdown and codespell clean/typo behavior | 🟢 | 🟢 | 🟢 |
| Existing root Bazel labels use owner-selected versions | 🟢 | 🟢 | 🟢 |
| Ordinary uv project and uvx consume the generated codespell extra | 🟢 | 🟢 | 🟢 |
| Old M3 release rejected; fresh owner snapshots accepted | 🟢 | 🟢 | 🟢 |
| Prepared installation skips both tools; APT and unmigrated selections remain | 🟢 | 🟢 | 🟢 |
| Smaller repository selection retains the same nine commands | 🟢 | 🟢 | 🟢 |
| Fresh complete DevContainer image for the changed selection | 🟡 Not rebuilt | 🟡 Not rebuilt | 🟡 Not rebuilt |

Green means the stated bounded check passed, not that the whole migration is
finished. The shared offline protocol probes ran as UID 1000 for mise and Nix,
and UID 0 for aqua. This checkpoint does not establish equal production-user
coverage; the earlier full-image milestone records its own user conditions.
Root Bazel and uv consumer checks allowed networking.

## Execution overhead is a separate open criterion

The [confirmed execution-path requirement](tooling-execution-paths.md) applies
to all tools, not only uvx. M4's functional checks do not establish acceptable
startup overhead or the absence of hidden launcher work. The comparison there
tracks a separate audit of native and Python invocation chains, direct prepared
execution, and provisioning cost versus repeated startup. No candidate has a
performance rating from this milestone.

## What the implementation says about complexity

The recurring edits and the repairs exposed by this exercise are different:

| Maintenance criterion | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Author native selection | GitHub backend identity, exact version and profile | Exact version/profile, local recipe and allowed registry identity | Existing package attribute and profile; version follows locked Nixpkgs |
| Author Python selection | PyPI identity/version in native configuration | Direct requirement in Python dependency group | Native package attribute; generated Python version follows it |
| Shared integration metadata | Feature membership and Python distribution/entrypoint identity | Feature membership and Python distribution/entrypoint identity | Feature membership and Python distribution/entrypoint identity |
| Tool-specific compatibility work | Backend-to-command mapping; existing archive exporter handles starpls | Raw release asset/platform mapping in registry and Bazel exporter | Command/class registration and starpls-specific version probe |
| One-time prototype repair | Native-only published locks; missing executable mapping; producer root refresh/bootstrap reuse | Snapshot and validate local registry/policy inputs; remove fixed facade-version assumption | Reuse existing artifact hashes when selected version is unchanged |
| Package recipe added in this exercise | None | Local starpls release recipe | None |

The concrete extra work for aqua is now demonstrated: a package missing from
its pinned registry needs a recipe and policy, and its portable Bazel export
needs compatible asset mapping. mise's generic GitHub backend avoids owning that
installation recipe. Nix avoids it because this locked package set already
contains both packages. Nix's portable Bazel route still needs upstream artifact
metadata; selecting a Nix package does not remove that boundary.

All three still contain explicit command/class registrations in the prototype
adapters. These are real maintenance obligations; they are not generated away by
the manager. Conversely, fixing mixed native/Python locking or snapshotting a
new kind of owner input should not be charged again for every future tool.
The candidate ledgers classify the individual edits rather than treating every
changed file as recurring complexity.

This favors mise or Nix for **this missing-registry onboarding case**. It does
not establish a global winner: requesting an arbitrary version outside the
locked Nixpkgs set has not been exercised, and one missing aqua package does not
measure typical registry coverage. The next discriminating maintenance case is
an explicit version request that the current native package set does not offer,
with the same request and acceptance criteria in all three variants.

## Evidence and limits

The [shared behavior checker](../experiments/tool-manager-comparison/onboarding-runtime-check.py)
tests starpls's real initialize/shutdown protocol and codespell's real typo
diagnostic. The LSP probe does not assert project indexing or analysis. All three offline
probes logged a background Bazel Central Registry lookup failure despite a
successful protocol exchange. That cache/network condition is not a manager
capability ranking. Its
workspace carries the existing provider's Bazel selection so background discovery
does not accidentally request the latest release.

This checkpoint does not repeat the complete LLVM/APT/CodeQL image builds.
Milestone 3's full images remain evidence for their recorded selections; they
are stale against the new owners until rebuilt. Fresh producer outputs,
compatibility metadata, facade consumers and feature handoff are checked here.
Platform metadata is not an ARM/macOS execution claim. A broader arbitrary-version
request against Nix's package set also remains a separate maintenance question.
