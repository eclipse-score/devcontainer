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

# Cross-review before a second comparison round

Date: 2026-10-31. **Phase 1 only; recommendation suspended.**
No new execution tests, integration code or production changes were made for
this review. The existing experiment and its evidence remain unchanged.

Read the current primary decision record and the complete aqua/Nix reports,
configs and smoke/export scripts. Exchanged findings directly with both peers.
The primary record still contains the first provisional mise recommendation;
that is historical input under review, not the outcome of this round.

## 1. Claims to correct or qualify

### One interface is not evidence of lower maintenance

My first report established that mise's `install` orders configured uv before
`pypi:pre-commit`, and provides common version editing, bin discovery and config
environment mechanisms. It did **not** establish that this saves meaningful
maintenance over aqua `cp` plus ordinary uv environment/install commands.

Mise itself uses aqua recipes and uv. It moves common orchestration into an
upstream manager, but does not remove those backends, runtime choices, release
selection, package availability or our delivery adapters. The aqua experiment's
native YAML plus direct Python requirements are allowed by our requirements.
Two backend config files are not an architectural deficiency. Conversely, a
single mise command is useful convenience, not a measured maintenance win.

The common workflow must count maintained decisions and custom glue, not manager
names, source lines or shell commands. There is no demonstrated winner here yet.

### My profile and lock policy is not free

The final mise experiment uses separate native/Python config environments so
native artifact hash locks do not cause optional PyPI dependency-graph locking.
It also uses an explicit `-E native,python` selection, expanded to
`native,python,repository` for the repository overlay. This is native support,
but adds conventions maintainers and launchers must understand. The empty common
config and isolation harness are experiment choices, not unavoidable mise costs.

Aqua tags give native memberships at each package declaration. Its peer found
that tag-filtered `install` can still create proxies/lazy-install other tools;
`cp --tags` is the relevant fixed-provisioning operation. Nix's selection lists
are explicit reusable subsets. We should transfer these approaches rather than
judge one candidate by an unsuitable command or by file counts.

### Bootstrap and runtime requirements must be symmetrical

My fresh mise install demonstrates operation without an authored Python runtime
pin on this Linux host. It does not prove operation on every machine without a
usable Python runtime. uv is still a configured helper, and Python availability,
auto-download behavior, persisted venv paths and execution permissions remain
runtime facts to account for. Aqua plus uv has the same class of Python/runtime
choices. A system hook's additional interpreter is a consumer dependency, not a
new manager requirement.

Nix owns its interpreter/dependency closure through existing package recipes.
Its bigger bootstrap and store are real differences, but copying just Ruff's ELF
out of that closure is not a fair container-integration acceptance test. The
prepared complete closure must be allowed as its native runtime layout. Actual
Ubuntu/non-root use has not been established by any of these first-round probes.

### Bazel export evidence differs in depth, not proven maintainability

Aqua actually built/ran Ruff via its generated Multitool metadata. My mise
export only matched existing metadata. The former is stronger integration
**evidence**, not proof that aqua has a generally superior export API. Both
export scripts encode Ruff's archive naming/layout. Neither proves export for
all existing simple tools, aliases or auxiliary files.

The aqua peer inspected its CLI and found no resolved multi-platform recipe
export that would remove this mapping: `cp` yields executables for the current
platform, not Multitool's URL/archive metadata. My mise lock likewise carries
URLs/hashes but not the complete installer recipe. Both may rely on upstream
registry recipes during installation while still owning additional layout
knowledge in a Bazel metadata bridge. Registry maintenance must be distinguished
from maintaining that bridge. Do not invent a universal recipe translator.

Mise's registry/checksum/provenance policy should also be documented as carefully
as aqua's explicit registry pin and checksum settings; this first experiment did
not establish equivalent registry update ownership just because tool pins match.
GNU-versus-musl Ruff artifacts are not an unmet requirement: version equality is
the confirmed target, and platform-specific artifacts are allowed.

### Nix independent updates need not mean a bespoke recipe

The Nix peer confirms that a second locked Nixpkgs input can supply pre-commit
while Ruff remains from the original input. This uses existing package recipes,
not a handwritten dependency tree or necessarily an overlay. Costs are an extra
package-set pin/fetch and finding/reviewing a suitable revision. A single package
set can update several tools together; that is not the only native workflow.
This method is source/peer-derived at this stage, not newly executed evidence.

### uv-only release selection is equally unfinished

All three candidates can supply selected versions to uv. None has completed the
exact published Git-release Python-runner interface. My generated Starlark file
is a metadata example, not proof of that consumer path. Aqua demonstrated a
requirements-based invocation and Nix demonstrated an exported version consumed
by host uvx. They are useful stronger observations for those respective paths.

If direct manager invocation is accepted for #189, give all candidates that
option. If a uv-only consumer is required, compare each candidate's release
metadata/package adapter under the same restriction. Do not credit mise for
avoiding an adapter only by changing the consumer requirement.

## 2. Useful approaches to transfer

| Peer approach | What mise should learn or the protocol should retain |
| --- | --- |
| aqua `cp` uses official recipes and produces direct executables | Judge the prepared installed result and runtime ownership, not whether a manager shim starts successfully. |
| aqua requirements file plus explicit fixed venv | A small pair of standard backend operations can be maintainable; compare this directly to mise's shared install/path/profile conventions. |
| aqua's actual minimal Multitool workspace | If more bridge evidence is necessary, reuse the same minimal workspace/protocol; avoid an unrelated full-repository Bazel build. |
| Nix reusable selections and `buildEnv` | Use one clear environment membership model; do not invent arbitrary profile matrices merely to exercise mise flags. |
| Nix's network-disconnected repeat | Separate online preparation from execution and make runtime no-fetch observations equivalent for all candidates. |
| Nix JSON export consumed by host uv | Manager-free consumers are possible through derived release metadata; package-set selection need not require a manager on every consumer. |

## 3. At most three decisive common follow-up checks

These are proposals for the parent's Phase 2 protocol, not authorization to start
them independently. Aqua and Nix peers agree with these outcomes.

### Check A: a routine change reaches selected consumers once

Prepare two release/config revisions. Change one direct tool while the other
remains unchanged, and add/remove one environment membership. Record exactly
which authored and generated files change and which commands maintainers run.
Evaluate selected versions and intended memberships from the same definitions
for the host and image-provisioning outputs. Distinguish intentional installation
caches from the new environment selection; stale ambient PATH tools must not
masquerade as selected members.

Equivalent success: no second maintained version pin; the requested version
change reaches intended consumers; the unaffected tool stays as intended; the
new membership is observable. Different historical versions are acceptable.
Use each candidate's ordinary native workflow, including a second locked Nixpkgs
input if that is the normal bounded way to avoid collateral package updates.
Expose its actual extra decisions rather than assuming it is free or impossible.

### Check B: selected-release invocation behaves correctly outside its checkout

From a temporary nested consumer Git directory, select a prepared release and
run pre-commit (and Ruff if required for the shared invocation). Put a conflicting
executable on PATH and unrelated tool-manager config in the consumer directory.
Observe tool version, caller cwd/config discovery, argument forwarding and
success/failure exit status. Preparation may fetch; the pinned invocation must
not accidentally select consumer-local versions/config or arbitrary PATH tools.

Equivalent success: a consumer selects one release and gets its intended tool
without Container or Bazel, with preserved command semantics. Compare the
manager-native entrypoint for all candidates. If uv-only remains a requirement,
add the **same** uv-only variant for each, using derived metadata rather than
requiring a full public package implementation for just one candidate.

### Check C: prepared tools run directly in the intended non-root layout

Provision the same small selection into the proposed Ubuntu-compatible runtime
layout. Include the full Nix closure where needed and Python venv/interpreter
paths for all candidates. As a non-root user, execute Ruff and pre-commit
directly with no runtime manager invocation and no network access. Record which
paths/artifacts must be retained, their ownership/permissions and the necessary
build-time commands. No full S-CORE image or legacy special-case migration.

Equivalent success: installed pins start and perform the existing small fixture
checks under the agreed container trust model. No new custom installer/closure
framework is allowed just to obtain a passing candidate result.

## 4. Existing evidence that does not need gratuitous repetition

- All candidates already execute Ruff's F401 fixture and pre-commit with a local
  system hook. They already establish basic Linux startability and exit behavior.
- Existing Ruff/pre-commit versions need not be forced onto Nix as an artificial
  requirement. The initial versions and differing package identities are recorded.
- Aqua's actual Ruff Multitool run remains valid. Mise's matching metadata is a
  narrower result; a duplicate benchmark must not downgrade aqua's existing proof.
- macOS ARM metadata/resolution/evaluation exists for all three. Repeating Linux
  tests cannot close the actual Mac-execution gap, and no candidate may claim it.
- Nix already passed its prepared fixture test with its container disconnected
  from the network. That part is evidence; Check C adds the missing Ubuntu and
  non-root runtime context rather than pretending there was no offline test.
- Mise's separate native/Python configs and fresh version-only installation are
  established. Repeating the unwanted full Python dependency-lock path adds no
  decision value unless equivalent stronger guarantees become a requirement.
- Both bounded native exporters own archive-layout knowledge. Counting their
  roughly similar line lengths is not a controlled migration-cost comparison.

## 5. Phase 1 conclusion

The previous preference for mise based on “one manager” or “less orchestration”
is **not demonstrated**. Mise remains credible; so do aqua plus uv and Nix under
their native scopes. The next recommendation should be based on the three shared
observable outcomes and explicit remaining ownership, including registry updates,
profiles, runtime bootstrap, release selection and the bounded Bazel bridge.
No adoption recommendation is made in this review.
