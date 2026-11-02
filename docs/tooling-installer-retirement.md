<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Installer retirement: what changes the effort decision

**Historical pre-M5 assessment:** the subsequent
[installer deletion milestone](tooling-retirement-milestone.md) implements these
removal boundaries. Statements below about retained installers and missing strict
host paths describe the earlier probes, not the final M5 source.

This follow-up checks the deletion boundaries left open by the
[initial effort assessment](tooling-effort-conclusion.md). It includes actual
remaining-tool probes in each candidate, a working managerless host/update
control, and a bounded invocation measurement. It evaluates the consolidated
local reference, not the untouched upstream repository. Nothing is adopted,
committed or published by this investigation.

**Operational follow-up:** the [recovery, integrity and selection comparison](tooling-operations-comparison.md)
adds executed failure/recovery probes and distinguishes native manager capabilities
from the integration work assessed here.

## The shared architectural constraint

The native artifact definitions already feed existing public Bazel labels,
including `apm` and `opencode`. They describe portable release URLs, hashes and
archive layouts. Keeping those labels means retaining that information, either
as authoritative inputs or as generated output with a maintained exporter.
Nix package-source hashes do not substitute for portable release-asset hashes.

That makes the baseline structurally relevant: its existing generic container
installer consumes the same artifact descriptions that Bazel needs. A manager
can replace its install engine and upstream recipe maintenance, but must also
supply those existing Bazel descriptions. Equal functional results therefore do
not imply equal ownership, nor do they justify a manager by themselves.

The Python consumer path is common work: generate normal dependencies from
selected pins, publish/bind them to a SCORE release, and let the consumer use
ordinary Python tooling. The managerless control has already demonstrated this
without adding a runner.

## Exact remaining callers and removal boundaries

The [tracked-caller inventory](../experiments/tool-manager-comparison/retirement-evidence/baseline.callers.json)
includes hidden feature directories. These are the remaining categories, rather
than estimates from file or line counts:

| Caller or contract | Work required to retire native/Python installation |
| --- | --- |
| s-core-local feature `environment ...` runtime call | Provide its entire native/Python selection through the chosen route, including apm/opencode; leave APT and lifecycle setup intact |
| bazel-feature runtime call | Provide bazelisk/buildifier/starpls through the chosen route; retain Bazel prefetch/completion and compile-commands setup |
| Root `.devcontainer/post_create_command.sh` | Replace the unprepared `environment repository` native/Python install before removing the fallback; retain hook registration and builder setup |
| Feature build/cleanup phases | Keep APT temporary-package handling; these calls do not justify keeping the native download engine |
| `load_feature_versions.sh` and optional dive setup | Keep metadata queries for provider versions; no need to keep native extraction for these queries |
| Feature verification and Python-runner regression | Retain observable verification and public argument/cwd/exit behavior; adapt tests that happen to invoke an internal installation command |
| Renovate and daily job allowlist | Change both the update command and the CI permission configuration when native pins become generated; the release refresh workflow cannot simply disappear |
| Public Bazel/standalone tool interfaces | Preserve or explicitly migrate them; these interfaces do not automatically make `tools/internal/devcontainer/install.py` subcommands permanent public APIs |

After migrating those callers, the native `_cmd_install`, `_place_binary`,
`_extract_member`, `_extract_dir` and their now-unused lockfile lookup helpers
can be removed from the container installer. `_cmd_install_python` and its CLI
registration can likewise disappear when the feature and repository installation
routes are replaced. OS/CPU detection used by verification, catalog validation,
APT policies, metadata queries and provider lifecycle remain.

This is a specific removable responsibility, **not removal of the whole
installer module**. None of those deletions has been applied to the accepted
M1–M4 worktrees in this investigation. The existing unprepared starpls fallback
was preserved for the M4 experiment; the audit found no documented public
installer-subcommand promise requiring that implementation forever.

## Managerless control: real provisioning and a real update

The [host proof](../experiments/tool-manager-comparison/retirement-evidence/baseline.host.json)
records fresh existing-catalog native installs of Ruff 0.11.13, ShellCheck
0.10.0 and starpls 0.1.22, plus pre-commit 4.7.0 through the existing uv adapter,
all into task-owned directories. Installed commands ran by absolute path with
`PATH=/usr/bin:/bin`; Ruff F821, ShellCheck SC2086 and pre-commit configuration
validation worked. Their ordinary direct calls need neither Bazel nor a newly
adopted manager.

The discovered ShellCheck archive-member update bug is now repaired in
`tools/internal/refresh_lockfile_digests.py`. Its regression failed for both
version-bearing `file` and `dir` fields before the fix and passes afterwards.
The existing missing-digest/no-write regression still passes.

A subsequent **actual** temporary update to ShellCheck 0.11.0 fetched upstream
release metadata through `gh api`, derived fresh URLs/hashes/member paths,
downloaded the selected Linux archive, verified it, extracted it and ran
`--version` successfully. The
[updated metadata](../experiments/tool-manager-comparison/retirement-evidence/baseline.shellcheck.lock.json)
and [refresh record](../experiments/tool-manager-comparison/retirement-evidence/baseline.update.json)
are retained. The production version pin is unchanged. This real update is
separate from the earlier synthetic fixture with mocked hashes.

The baseline still owns the installer and update assumptions. Fixing this
bounded bug does not claim automatic support for arbitrary upstream layouts,
native-host public API completion, all-platform validation or release hosting.

## Execution cost is separable from manager choice

A [common warm invocation probe](../experiments/tool-manager-comparison/retirement-evidence/baseline.warm-startup.json)
ran the same starpls 0.1.22 `version` command directly, through a shell script
containing only `exec`, and through the existing Bazel target.

| Invocation | Median | Observed range |
| --- | --- | --- |
| Installed binary directly | 1.013 ms | 0.974–1.463 ms |
| Thin shell forwarding to that binary | 1.240 ms | 1.118–1.390 ms |
| Warm Bazel target | 91.806 ms | 86.211–140.909 ms |

Conditions: one Linux amd64 host, two warmups per route, 20 interleaved samples
per route, existing warm Bazel server/cache, other investigation jobs possibly
active. This is a local observation, not a product benchmark, cold provisioning
measurement, numeric acceptance budget or manager ranking. The Bazel-resolved
artifact has the same declared release; binary identity across routes was not
asserted. The thin-shell/direct pair uses the very same installed binary.

A [source inspection of actual prepared codespell entrypoints](../experiments/tool-manager-comparison/retirement-evidence/prepared.launchers.json)
shows direct Python shebangs for mise/aqua and a Nix store shell environment
wrapper followed by the Python script for Nix. Those sampled scripts do not
call a manager/resolver. M4 separately executed their behavior. This is a bounded
source audit, not exhaustive dynamic tracing of every tool.

All variants can expose prepared commands directly. Default aqua proxies,
manager execution commands and Bazel remain distinct optional invocation paths;
they must not silently become the only prepared execution route. The public
strict-host runner still uses Bazel in the current references: adopting a
manager alone does not complete its fast pinned replacement.

## Remaining native packages: the distinguishing cases

These are the actual existing pins, not hypothetical complex tools added to
make one candidate fail. Existing M4 configs/releases were left unchanged;
new candidate-native inputs and installations live in task-owned directories.

| Concrete case | Consolidated baseline | mise | aqua + uv | Nix |
| --- | --- | --- | --- | --- |
| Existing starpls 0.1.22 | Existing portable artifact recipe | Generic GitHub backend; no local installation recipe | Local registry recipe at the pinned standard-registry gap | Existing package |
| Existing APM 0.35.0 | Existing archive-directory recipe retains runtime/data | Generic GitHub backend installs the full tree | Missing standard entry; local recipe works, but `cp` of the executable alone loses its runtime/data | Exact existing `pkgs.apm-cli`; first lookup under `pkgs.apm` was a naming miss, corrected |
| Existing OpenCode 2.2.3 | Existing portable artifact recipe | Existing aqua backend; exact release works | Existing standard-registry package; exact release works | Locked package is 2.2.1; exact 2.2.3 works with a local binary derivation |
| Direct execution after installation | Actual native and Python commands verified | Direct installed paths/symlinks; manager not mandatory at each call | Direct resolved paths work; default aqua-proxy links are a different path | Store executable/runtime wrappers; Nix evaluation not mandatory at each call |

For mise, both last tools installed at the exact requested versions. The native
lock covered the existing four Linux/macOS platform artifacts, with hashes
matching the catalog; execution was Linux amd64 only. Its GitHub backend keeps
APM's embedded Python and `_internal` resources without a new installation
recipe. APM needs Git available; that is a tool dependency provided by the
existing environment, not a per-call manager requirement.

For aqua, the successful APM path is `install` followed by retaining the whole
package and exposing its resolved executable. The earlier fixed `cp` recipe
used successfully for single-file tools is insufficient for this package. That
is a specific runtime-handoff adaptation, not lack of support. The local recipe
and policy are additional maintenance. A default-branch file lookup also found
neither APM nor starpls at their expected registry package paths on this date;
this was not merely an assumption that the pinned registry was old.

For Nix, APM's correct attribute exists at the exact version and works. OpenCode
requires an explicit version intervention against this package set. The parent
independently completed a small binary derivation using the existing verified
release asset, runtime library inputs, `autoPatchelfHook`, a runtime wrapper and
`dontStrip = true`. Actual `--version` and `--help` passed at 2.2.3; see the
[exact-package proof](../experiments/tool-manager-comparison/retirement-evidence/nix.exact-opencode.json).
Preserving the embedded application payload matters: stripping the binary
produced a successful build whose CLI did not work. The existing Nixpkgs recipe
already documents this through `dontStrip`.

The candidate also completed a source-build fallback and the parent re-ran its
exact 2.2.3 version successfully; the
[final Nix record](../experiments/tool-manager-comparison/retirement-evidence/nix.retirement.json)
retains both routes. That source route updates the source archive hash and a
generated Bun dependency-tree hash, rather than hand-authoring each transitive
dependency. Those dependency hashes and the source build graph are **not mandatory** for the working binary route above, and must
not be counted as the only possible cost of using Nix. Finding another suitable
Nixpkgs snapshot is another valid version-selection strategy; none was proven
here. The default-branch OpenCode recipe also still reported 2.2.1 at lookup
([record](../experiments/tool-manager-comparison/retirement-evidence/nix-latest-opencode.json)).
The local binary derivation is an executed example of extra package ownership,
not proof that every independent Nix version requires one.

## Final effort recommendation for the current requirements

**Use the consolidated managerless architecture as the current target.** Add the
ordinary release-selected Python dependency package and a deliberate install-once,
direct-execution host interface. Keep the existing shared portable artifact
catalog and bounded generic installer rather than introducing a second native
owner/export/installation lifecycle now. The host proof is evidence for the
mechanism; its internal Python installer is not already a finished public host
API, and requires Python during provisioning. Release publication, native host
bootstrap policy and macOS execution remain explicit completion work.

This recommendation replaces the earlier provisional preference for aqua + uv:

- The baseline already shares artifact knowledge between the required Bazel
  path and container installation. A new manager does not remove the need for
  that portable metadata and its verification.
- The Python consumer requirement works without any candidate manager. Its
  exporter, release integration and hosting are common work, not manager value.
- The actual remaining-tool probes expose costs hidden by the smaller examples:
  aqua needs another local recipe and a whole-runtime-tree path; Nix needs an
  independent version/package decision; mise handles the installations but
  still needs the compatibility exports and caller migration.
- Migrating feature installs, repository setup, updates and export conventions
  adds one-time work. Retaining both old paths and prepared-runtime machinery
  indefinitely would also add recurring work. No demonstrated deletion offsets
  that combined introduction in the present scope.

**If a standard native manager is nevertheless desired, mise is now the strongest
alternative in these concrete cases.** Its generic backend handled both registry
gaps (starpls/APM), and it installed the requested OpenCode version while keeping
APM's full runtime tree. Use it only for provisioning and expose direct commands;
prefer direct feature/repository provisioning over mandatory out-of-band handoff.
Its native/Python lock convention and Bazel exporter remain real responsibilities.
This is a qualitative effort judgment grounded in observed operations, not a
claim about all registry packages or engineering hours.

Aqua is still workable, but the original argument that its narrow copying model
is simpler does not cover APM's full tree or the local recipes now demonstrated.
Nix is also workable; its added runtime/package model is justified when owning
runtime closures is a desired outcome. The present requirements keep Ubuntu/APT,
external features and complex tools, so that additional model has not displaced
the existing one.

The candidates are therefore **not equivalent in value for this repository**:
the baseline meets the mechanisms with the least new architectural commitment;
mise offers the clearest demonstrated upstream installation reuse; aqua requires
more local exceptions for the tested inventory; Nix offers broader dependency
ownership than the current problem calls for. Long-term incident/update hours
remain unknown. No file-count score or invented effort percentage is needed to
make this recommendation.

The [dynamic execution audit](tooling-execution-paths.md#dynamic-execution-audit-what-actually-happens)
now observes the prepared native/Python process chains and measures their paired
startup cost. It finds no manager/resolver/Bazel call in those samples and verifies
signal behavior. That removes a runtime objection to all three candidates; it
does not remove their different maintenance and integration responsibilities.

## What is complete, and what is not claimed

The investigation closes the questions about remaining callers, exact native
availability, actual runtime-tree requirements, removable duties, common Python
work and optional versus mandatory launchers. It also repairs and verifies the
bounded baseline update bug. The three accepted implementations remain intact.

It does not claim that installer retirement or the complete migration has been
implemented, that native host bootstrap/public APIs are finished, or that all
platforms and release automation are production-ready. Those are implementation
work after choosing the target, not reasons to repeat equivalent feasibility
tests across all three indefinitely. This recommendation is ready for review;
it does not itself adopt a manager, delete compatibility or publish artifacts.
