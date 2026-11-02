<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Operational comparison: recovery, integrity and removing tools

**Status:** local experimental evidence, 2026-11-01; no architecture adopted.
This extends the [effort conclusion](tooling-installer-retirement.md) with three
operations that expose responsibilities beyond a successful initial install.
They are decision criteria, **not newly imposed product requirements**.

The important new distinction is that **Nix supplies installed-tree verification
and repair**, whereas **mise supplies reusable artifact downloads once the lock
has been prepared appropriately**. Aqua and the existing installer need a
separate recovery arrangement for this fixture. All four can still expose fast,
direct tool commands; these maintenance operations add no required per-call
manager or integrity check.

## Questions and observed results

Every case uses starpls **0.1.22 on Linux amd64**, isolated from accepted candidate
caches. Offline commands run in Docker with `--network none`; the non-Nix tool
operations also run as a non-root user. Nix owns a separate disposable store.
🟢 means demonstrated native support with the stated preparation; 🟡 means extra
preparation or an important limitation; 🔴 means the specified operation did not
achieve its outcome. These are cell results, not an overall candidate ranking.

| Concrete criterion | mise 2026.10.24 | aqua 2.65.2 | Nix, existing locked package | Existing installer, managerless control |
| --- | --- | --- | --- | --- |
| **O1: Delete the expanded package; reinstall offline from the state retained by normal installation** | 🟡 Fails with the accepted lock's `checksum_source = "mise-versions"`; passes after the separate preparation described below | 🔴 No archive recovery after removing this expanded package; installer attempts GitHub access and is stopped after 25 seconds | 🟡 Fresh store import passes **after explicit file-cache export of the package and closure**; this is an additional preparation step | 🔴 Reinstall uses the original remote URL and fails; no persistent artifact cache in this installer |
| **O2: Detect changed installed bytes even when the tool still reports the pinned version** | 🔴 Ordinary install skips the existing tool; it does not detect the changed executable | 🔴 Ordinary install succeeds while retaining the changed executable | 🟢 `nix store verify --no-trust` detects the modified store path | 🔴 The version probe still succeeds; failed offline reinstall does not provide an installed-tree integrity diagnosis |
| **O2: Repair those bytes without contacting upstream** | 🟢 With the independently checked lock and cached archive, `install --locked --force` restores the original executable hash | 🔴 Re-running install retains the changed file; after removing the package, native reinstall cannot recover it from the remaining state | 🟢 `nix store repair` restores the original hash from the exported local file cache; subsequent verification passes | 🟡 An explicit local `file://` artifact mirror plus a temporary lock restores the original hash through the existing checksum-checking installer |
| **O3: Remove a tool from the active native selection while retaining cached packages** | 🟢 Removing the config entry and regenerating `mise env --paths` removes its managed path | 🟢 With `packages: []`, native `aqua which starpls` fails | 🟢 `nix profile remove` removes `profile/bin/starpls`; the package need not be garbage-collected | 🟡 Applying an empty named environment leaves the existing destination executable in place; no separate native activation profile |
| **O3: Apply an empty selection over an existing fixed export directory** | 🔴 The previously exported executable remains; config activation does not clean an independently copied bin directory | 🔴 `aqua install` followed by `aqua cp` with an empty selection leaves the old exported executable | 🟢 The tested native profile link reflects the new selection; an independently copied bin directory would still be our responsibility | 🔴 Applying the empty selection leaves the old destination executable |

The O3 operations deliberately distinguish **native activation** from **copied
exports**. The Nix test uses its native profile operation, not a claim that its
package store deletes unselected tools. The mise test regenerates PATH entries,
not a claim that editing a config updates existing shells. Aqua's native command
lookup is not proposed as a mandatory runtime wrapper. None of these observations
makes cache retention itself a defect.

## O1: A usable cache requires an explicit preparation policy

The accepted mise lock obtains its checksums from mise-versions. For this fixture,
a successful online locked install left no reusable archive in `downloads-cas`.
Deleting the expanded version and installing offline failed. Reinstallation with
`--force` also failed with that state.

A second, independent fixture used ordinary `mise lock --platform linux-x64`
with `MISE_USE_VERSIONS_HOST=0`, then `mise install --locked`. The generated lock
contains the **same archive URL and checksum**, without the mise-versions marker.
Its archive is retained in the native download cache. Both offline forced repair
and offline reinstallation after deleting the expanded package pass.

This matches the documented distinction between metadata-supplied checksums and
checksums checked against a download: a marked checksum is not used to reuse a
kept artifact. We did not remove the marker by hand or weaken checksum checking.
See the [mise lock explanation](https://mise.jdx.dev/dev-tools/mise-lock.html#checksums-from-mise-versions)
and [download cache settings](https://mise.jdx.dev/configuration/settings.html#download_cache).
The original candidate lock is unchanged.

For aqua, the fixture retains its registry, checksum data and manager state but
removes the expanded starpls package. Native reinstall attempts to fetch the
GitHub release. It does not reconstruct the package offline within the bounded
attempt. This does not rule out a registry using a separately maintained local
artifact mirror, or restoring an entire package-directory snapshot. Neither is
an archive cache demonstrated by this normal install path.

Nix exports the selected store path **and its runtime closure** with
`nix copy --to file://…`. A fresh, network-isolated store then imports from that
file cache. This is stronger than keeping the executable alone, but requires
that explicit export and a cache retention/distribution policy. It does not mean
that deleting a Nix store magically preserves its contents elsewhere.

The control demonstrates that a manager is not necessary for a small offline
artifact mirror: the existing installer accepts a local URL and verifies the
original catalog checksum. Creating, publishing and selecting that mirror would
remain SCORE work. The temporary fixture lock is not a proposed second source
of production pins.

## O2: Download verification and installed-tree verification differ

The probe appends benign bytes to each disposable executable. Every changed
executable still prints the correct version. Independent SHA-256 comparisons
confirm the byte change. A passing version check therefore does not demonstrate
unchanged installed content.

mise and aqua both accept the existing installed package on a normal install.
The installer control attempts to download again; without networking it fails
before replacing the changed file. This is distinct from detecting the changed
installed content. With a prepared local artifact source, reinstallation restores
known bytes in both the mise and installer cases.

Nix diagnoses a changed NAR hash for the selected store path. Repair from the
previously exported file cache restores the original executable hash and makes
`store verify` pass again. Nix automatically disables substitution when it detects
no networking, so the repair command explicitly enables substitution and allows
**only the local file cache**. The fixture permits unsigned local cache entries;
it does not establish a production cache trust/signing policy.

The changed-file probe is accidental-corruption detection, not an adversarial
security audit. A trusted installation or container is still trusted at execution
time under the agreed contract. No proposal here adds hashing before each tool
invocation.

## O3: Selection changes need a publication operation

Replacing a selection and installing into an existing bin directory is additive
in the tested control and aqua export paths. Removing a tool from configuration
does not remove that old executable. A copied mise export has the same property.
Native mise activation, aqua lookup and a Nix profile do reflect the removal,
but each has a different exposure mechanism.

The architectural consequence is concrete: if SCORE publishes a fixed directory
of direct commands, it must define how that directory is replaced. Preparing a
fresh release prefix and switching the active link can provide this for any
candidate; Nix already demonstrates a native profile mechanism. Existing shells,
old absolute paths and independently copied executables require separate care.
This experiment does not claim an atomic release publisher, rollback protocol or
interrupted-update recovery has been implemented for all candidates.

## What this changes in the effort assessment

| Responsibility | What we can now attribute to a candidate | What remains ours |
| --- | --- | --- |
| Rebuild a lost installation without upstream | mise's checked-download cache; Nix's closure export/import | Pick a preparation policy, persist the cache, distribute it and retain supported releases |
| Diagnose and repair altered installed content | Nix has verified native commands for both | Decide whether this capability is valuable enough to operate a Nix store/cache; other routes need an external installed-content manifest if diagnosis is required |
| Remove commands when changing releases | Native selection mechanisms work in all managers; Nix profile directly publishes the tested command set | Define fixed-prefix publication for direct commands and avoid stale additive exports |
| Managerless recovery | Existing verified downloader works with a local file mirror | Own mirror construction/selection, retention and any installed-content verification |

The earlier managerless recommendation remains the lowest **demonstrated
integration burden for the currently confirmed scope**; it is not a claim that
managers supply no additional capability. Nix now has a concrete operational
advantage if installed-content verification and closure recovery matter. Mise
provides a useful middle ground if retaining verified upstream artifacts is
valuable without adopting a Nix store. Aqua does not gain a demonstrated advantage
over those two from these operations.

These benefits must be weighed against the already demonstrated package/update
and Bazel-export ownership. No engineer-hour estimates or overall numeric score
can be justified by this small probe. In particular, an optional disaster-recovery
capability must not outweigh ordinary tool maintenance merely because it is easy
to measure.

The subsequent [execution audit](tooling-execution-paths.md#dynamic-execution-audit-what-actually-happens)
adds direct process/socket traces, paired startup costs and signal checks for the
prepared native/Python paths. Those are separate from recovery operations.

## Evidence and boundaries

The [reproduction instructions and fixture inputs](../experiments/tool-manager-comparison/operations-evidence/README.md)
explain preparation separately from offline execution. The
[probe driver](../experiments/tool-manager-comparison/operations-probe.py) records
commands, network isolation, exit status and hash-based assertions. Candidate
records are linked there.

This is one native tool on Linux amd64, not Python environment recovery, macOS
execution, proxy support, simultaneous updates, cache eviction, full-image
recovery or proof of reproducible source builds. Provisioning uses local Docker
runtimes to isolate networking; that does not count as native macOS coverage or
a newly delivered host installer. The tested Nix package has a runtime closure,
whereas the other fixtures use the upstream native release asset. Cross-candidate
executable hashes are not compared: only each candidate's own before/after hash
must match.
