<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M5: compare the implementations after deleting the replaced installer

The [M6 integration comparison](tooling-integration-milestone.md) supersedes this
checkpoint for command deselection, dependency packages and integration results.

**Status, 2026-11-02:** installer removal implemented in all three worktrees;
focused checks pass; fresh full-image gates remain pending. No candidate is
adopted; nothing is committed, pushed or published. This follows the
[M5 outcome contract](../experiments/tool-manager-comparison/retirement-milestone.md).
The earlier [retirement investigation](tooling-installer-retirement.md) describes
the pre-M5 state, including fallback code which M5 now removes.

## What this comparison measures

The question is which maintained responsibilities survive a completed migration.
Prototype line counts, evidence files and time spent by an agent do not measure
that. A delegated installer still needs bootstrap and integration; a generated
Bazel catalog still needs an exporter. Conversely, keeping APT and specialized
Dev Container features does not mean that native download/extraction has survived.

All three worktrees started from the same consolidated reference and inherited
their M1–M4 experiments. They receive the same removal boundary: every selected
native/Python tool, repository setup, image setup, prepared direct host execution,
update automation and existing public compatibility. Ordinary Python dependencies
and uv/uvx consumers remain a common requirement, rather than a reason to prefer
one producer manager.

## Actual deletion boundary

The old `tools/internal/devcontainer/install.py` native installation path and
Python tool installer are removed in all three variants. The deleted functions
include `_cmd_install`, `_place_binary`, `_extract_member`, `_extract_dir` and
`_cmd_install_python`; the `install` and `install-python` subcommands disappear.
This is deletion, rather than a manifest condition which bypasses a second engine.

The remaining module owns OS/package-provider setup, feature membership queries,
metadata and environment verification. CodeQL, LLVM, Java, optional features,
APT cleanup and Bazel completion/prefetch remain deliberate responsibilities.
Existing portable Bazel labels still consume generated release-asset metadata.

The root repository Dev Container deserves a separate caller check: it uses a
generic Node image, not the published SCORE image. Its post-create hook must
actually install the repository selection before registering pre-commit hooks.
Assuming that the published image has already done this is incorrect here.

## Where the remaining effort differs

Legend: 🟢 delegated by a usable existing mechanism; 🟡 explicit integration or
bounded local maintenance; 🔴 a substantial additional operating responsibility.
Colors describe the stated responsibility, not product quality or maturity.

| Concrete maintenance criterion | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Native archive extraction during installation | 🟢 Backend recipes replace our extraction engine | 🟢 Registry recipes replace our extraction engine | 🟢 Package/store deployment replaces our extraction engine |
| starpls at the selected release | 🟢 Generic GitHub backend | 🟡 Local registry recipe | 🟢 Existing Nixpkgs package |
| APM with its embedded runtime and data | 🟢 GitHub backend retains the package tree; expose its executable | 🟡 Local recipe plus retaining its complete package tree; copying only the executable is insufficient | 🟢 Existing `apm-cli` package |
| Exact OpenCode 2.2.3 | 🟢 Existing aqua backend | 🟢 Existing registry recipe | 🟡 Local binary derivation and runtime-library/embedded-payload handling against the selected package set |
| Python tool installation | 🟡 Existing PyPI backend; install-tree and entrypoint exposure remain ours | 🟡 Ordinary uv tool installation; environment/path exposure remain ours | 🟢 Package closures include Python runtimes/dependencies; selection/export remains ours |
| Remove a deselected command from a reused host prefix | 🟡 Current provisioner writes selected links; removal reconciliation remains ours | 🟡 Current helper copies/installs selected commands; removal reconciliation remains ours | 🟢 Profile replacement owns exposed membership; old store objects can remain until garbage collection |
| Portable Bazel URL/hash/archive-layout export | 🟡 Backend lock plus SCORE identity/layout mapping | 🟡 Registry resolution/checksums plus SCORE identity/layout mapping | 🟡 Separate upstream portable artifact recipes/hashes remain necessary |
| Existing Ubuntu/APT/external features | 🟡 Retained provider/lifecycle setup | 🟡 Retained provider/lifecycle setup | 🟡 Retained provider/lifecycle setup alongside the Nix store |
| Extra runtime deployment model | 🟡 Installed trees and direct links | 🟡 Installed trees and direct links | 🔴 Store closure production, transfer, activation and root/profile lifecycle |
| Ordinary Python package consumers and SCORE release binding | 🟡 Shared generation/release work | 🟡 Shared generation/release work | 🟡 Shared generation/release work |

An upstream registry recipe and a portable Bazel archive definition are different
contracts. Deleting the container extraction engine does not remove the need for
the latter. Likewise, native recipe availability does not automatically provide
our environment selections, update permissions or release-to-package binding.

The reused-prefix row is a source finding about the new M5 provisioners, not a
claim that a fresh image includes deselected commands. The
[earlier operational probes](tooling-operations-comparison.md) already distinguish
manager caches from command exposure. Neither installing a new selection nor
recording an owner digest automatically deletes previously exposed commands.
That remaining reconciliation duty must be included in a production plan.

## Learning transferred between the implementations

Review applies findings across candidates rather than accepting whatever an
isolated worker happened to implement:

- Prepared strict host calls select the installed pin directly. Existing Bazel
  fallback remains available for a missing prepared command. Preserving this
  fallback does not require a manager or Bazel on a normal prepared invocation.
- Live owners and update/build entry points move under `tools/`; experimental
  snapshots must not become competing version owners in dependency discovery.
- mise should use Renovate's existing manager for supported backends, rather
  than charge newly handwritten per-tool regex rules as inherent complexity.
- aqua's maintained Renovate preset supplies package/registry update matching;
  checksum refresh and compatibility generation still need a post-upgrade step.
- Python dependency groups have native PEP 621 Renovate support. Updating the
  source and the daily job's command allowlist is one integration change.
- Root post-create provisioning and hardcoded editor/runtime paths must be
  checked separately from provisioning the published image.

These update mechanisms are documented by
[Renovate's mise manager](https://docs.renovatebot.com/modules/manager/mise/),
[aqua's Renovate guide](https://aquaproj.github.io/docs/guides/renovate/) and
[Renovate's PEP 621 manager](https://docs.renovatebot.com/modules/manager/pep621/).
They reduce custom matching work; they do not prove our CI release flow end to end.

## Verification boundary

The [static audit](../experiments/tool-manager-comparison/retirement-audit.py)
records removed definitions/subcommands, remaining installer functions, production
call candidates and production references to experimental paths. It includes
hidden feature directories, Dockerfiles and the extensionless `tools/run-tool`.
Historical reports and generated runtime payloads are excluded from caller search.
Static absence alone does not establish successful host/image provisioning.

Final candidate check results are recorded in the
[M5 evidence](../experiments/tool-manager-comparison/retirement-m5-evidence/README.md).
The candidate reports contain exact commands and their individual limits.

| Current check | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Five obsolete functions and both installation subcommands absent | 🟢 Static audit | 🟢 Static audit | 🟢 Static audit; one retained negative test checks that the old CLI is unavailable |
| Current compatibility exports and generated overview | 🟢 Refresh/check passed | 🟢 Refresh/check passed | 🟢 Sync/release check passed against the relocated production owner |
| Selected native/Python tools, including APM and exact OpenCode | 🟢 Executed on Linux amd64 | 🟢 Executed on Linux amd64; APM full runtime tree checked | 🟢 Executed from the M5 Linux amd64 closure |
| Real strict calls with poisoned PATH: uv, uvx, Ruff, pre-commit and Ruff error/cwd/argv | 🟢 Direct/strict results agree | 🟢 Direct/strict results agree | 🟢 Direct/strict results agree in a network-isolated runtime using the M5 store |
| Existing runner/Python launcher Bazel contract tests | 🟢 Passed | 🟢 Passed | 🟢 Passed |
| Candidate Python unit checks | 🟢 18 passed | 🟢 20 passed | 🟢 23 passed |
| Root generic Node Dev Container | 🟡 Provisioning caller migrated; full lifecycle not executed in that image | 🟡 Provisioning and persistent remote PATH configured; config parsed, full lifecycle not executed | 🟡 Bootstrap/profile caller migrated; isolated lifecycle fixture passed, full generic-image lifecycle not executed |
| Fresh full M5 published image | 🟡 Not built | 🟡 Attempt interrupted; no completion | 🟡 First attempt failed on an executable bit, now fixed; no successful final rebuild |
| ARM Linux / ARM macOS execution | 🟡 Declared/exported where supported; not executed | 🟡 Declared/exported where supported; not executed | 🟡 Selection evaluated; not executed |

Test counts describe the checks run, not relative coverage or complexity.
The common [prepared-runtime check](../experiments/tool-manager-comparison/retirement-runtime-check.py)
uses real commands, a filename containing spaces, a failing Ruff diagnostic and
fake PATH tools/managers/Bazel which fail if selected. It compares stdout,
stderr and exit status against absolute direct invocation. This is a bounded
post-provisioning check, not a new cold-bootstrap or exhaustive process-tracing
claim. The earlier dynamic traces remain separate evidence.

Only about 2.5 GiB of disk remained after implementation and checks. Further
full builds were stopped rather than pruning unrelated shared Docker data.
Previous M3 full images are historical evidence, not a fresh M5 image gate.
The Nix first-build executable-mode failure is retained in the report; correcting
that mode and passing static checks does not imply the complete build passed.

## Effort conclusion after deletion

**Among these three manager implementations, mise currently needs the least
tool-specific package work for the actual inventory.** Its GitHub backend handles
the demonstrated starpls/APM gaps and its existing aqua backend handles OpenCode.
This is a conclusion about recurring package maintenance, not measured engineer
hours or an automatic adoption decision.

aqua remains a coherent choice for a narrow native-install role. Here that role
still requires two local recipes, explicit APM tree retention, and separate uv
orchestration. Its portable exporter also constructs the known upstream archive
names/layouts; the registry does not eliminate that compatibility adapter.
mise's exporter still carries archive-member exceptions too, but can take native
asset URLs and hashes directly from its lock.

Nix supplies additional useful ownership: runtimes/libraries travel with the
package, and profile replacement controls exposed membership. Its extra effort
is concrete as well: store production/transfer/activation, host Nix bootstrap,
and an exact OpenCode derivation alongside the retained Ubuntu/features model.
That is a good trade when owning runtime closures is itself a goal. The current
requirements do not require replacing that OS model.

The old objection that all three merely add a bypass around an untouched native
installer is now disproved: that code has been removed. A net effort advantage
over the **consolidated managerless baseline** still does not follow automatically.
The baseline already needs portable artifact metadata for Bazel and can also use
it for its generic installation engine; all three managers add bootstrap and an
export boundary while delegating installation recipes. The earlier managerless
control remains relevant. Keep it as the adoption baseline; prefer mise if we
choose to delegate installation through one of the three tested managers.

## What remains before calling a variant the complete migration

The next gates are fresh complete image/feature checks and the actual generic
Node post-create lifecycle, followed by the declared platform checks. Reused
mise/aqua host prefixes also need deliberate deselection reconciliation.
Ordinary Python package/release generation remains local reference scaffolding:
in mise and aqua the production export check still updates a generated reference
pyproject under `experiments/`; these are reviewed audit references, not duplicate
version owners. Production package identity, release hosting/binding and hosted
update/release execution remain work before adoption. No publication was tried.

These are named remaining duties. They are not a reason to keep the deleted
installation engine, redo equivalent feasibility probes, or report a whole-repo
migration percentage from this bounded milestone.
