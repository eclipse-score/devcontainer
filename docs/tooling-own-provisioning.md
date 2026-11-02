<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Option 4: consolidated own provisioning

Local implementation, 2026-11-02, branch `eval/tool-manager-own`. No manager
adoption, public package identity, publication or commit is implied. Inherited
dirty documentation and the archive-member refresh repair are preserved.

## Agreed scope and authority

The latest user correction narrows removal to **no longer offering a tool in
new dependency metadata, Bazel registrations and newly built containers**.
Existing releases and developer installations remain unchanged. Automatic host
uninstall, deselection reconciliation, rollback and shared-profile cleanup are
not requirements. Draft ownership-ledger/recovery work was removed rather than
retained to match optional peer prototypes. Safe updates still reject unrelated
files and user-replaced commands.

The existing `tools/lockfiles/*.lock.json` remain authoritative portable
artifact definitions, shared by Bazel and native provisioning. One release
decision owns all commands in a shared archive: uv owns uvx's repeated backend
version, with refresh deriving it and validation rejecting disagreement.
`tools/score_tools/python_tools.bzl` owns Python distribution pins and command
identities, including the language-server/pytest aliases. Ruff's ordinary
dependency extra derives from its native owner, not another Python pin.
APT policies, npm, base images, external features and special feature lifecycle
setup retain their existing owners and responsibility.

`sync_readme.py` generates/checks the inventory and unavoidable native Bazel
hubs/aliases. Python Bazel targets already derive from the literal catalog.
Deleting an owner and its environment memberships removes it from these new
outputs; direct dependency release generation omits removed tools. No expanded
transitive lock is introduced.

## Maintained paths

`tools/score_tools/provision.py` is the single native download/checksum/extraction
engine. It streams hashes, supports existing files/single archive members/full
runtime directories, rejects traversal and unsupported archive links, and stages
native trees before publication. Commands sharing an artifact are prepared
together so uvx can find adjacent uv; unselected siblings stay private. Python
environments are ordinary `uv tool install` results at stable absolute locations.
They default to the provisioning interpreter; `UV_PYTHON` may select another.
They retain an interpreter dependency and are not relocatable runtime closures.

`tools/internal/provision.py` prepares native/Python environment selections or
explicit small selections in a user-selected prefix. No new manager, daemon,
recipe registry, activation shell or ownership database is required. Existing
feature and repository callers continue through `devcontainer/install.py`,
which now delegates to the same engine while retaining APT/npm, verification
and provider setup. Its compatibility install commands do not duplicate native
extraction or Python resolution engines.
Superseded container extraction and automatic lockfile-discovery helpers are
removed; platform detection and native catalog validation are shared rather
than copied into the container adapter.

Package directories are keyed by artifact/definition content, with completion
markers. Repeated preparation reuses complete packages; download failures are
reported and retried at most three times. Publication preflights all selected
names and replaces only links into the dedicated prepared package tree. A
prefix lock serializes updates; links are replaced individually, not as a
transactional whole-profile switch. There is deliberately no uninstall or
automatic garbage collection. Unfinished Python environments fail explicitly
and require a fresh data directory; corrupted installed bytes are not silently
attested by a version check.

**Migration:** use a fresh prefix; no regular files, foreign symlinks or old
copied installations are automatically adopted. Resolve a conflict explicitly
or select another prefix. New images start from their base and build selected
offerings; layering this provisioner over an old copied installation is not an
implicit migration. No unknown state-schema migration is needed because no
ownership database is introduced.

Prepared commands run directly. Optional strict host `tools/run-tool` uses the
explicit `SCORE_TOOLS_PREFIX`'s prepared links without manager/Bazel resolution,
sync or network; the existing applicable Bazel fallback remains. Container
commands stay trusted, including strict mode. Host convenience still permits
PATH. This does not claim per-call adversarial attestation.

`tools/internal/dependency_package.py build/check` generates a normal empty
dependency wheel with per-tool extras and `all`. Release version and local
identity are explicit. A manifest binds owner file hashes, rendered project
metadata, wheel identity/dependencies and wheel digest; check rejects stale
owners/metadata and changed wheel bytes. Consumers receive only ordinary
dependencies and need no producer source, container, Bazel or SCORE runner.
The existing optional `score-tool` API remains compatibility, not the new path.

## Real update and release operations

For a native update, edit its release version once, run
`tools/internal/refresh_lockfile_digests.py TOOL.lock.json`, review upstream
URLs/hashes/archive members, and run `tools/internal/sync_readme.py`.
Refresh remains owned work; it does not discover arbitrary upstream layout
changes. Python updates edit their literal owner once. Validate the affected
delivery paths, then build/check a dependency wheel with an explicit release
version and chosen identity. Hosts rerun provisioning into the same dedicated
prefix; ordinary Python projects change only their facade release requirement
and run uv lock/sync. New images consume those same source owners.

`tools/tests/release_smoke.py --output FRESH_DIRECTORY` exercises isolated owner
snapshots, leaving inherited production pins unchanged. A 0.8.0 local facade
selects Ruff 0.11.13; B 0.8.1 selects 0.14.6. Changed owner/stale artifact data is
rejected before refresh; A is rejected against refreshed B owners. Both wheels
pass owner-bound checks. The **same independent uv project** changes only its
facade version, and actual uv/uvx resolves the generated Ruff pin. The same
native prefix updates Ruff while preserving Buildifier's path/hash and a user
sentinel. The actual public `//tools:ruff` runs B and reports F401/exit 1 for
`bad input.py` from a caller subdirectory. Wheel metadata, consumer locks,
owner snapshots and command records are compactly archived; no payloads are.

## Comparison boundary

| Responsibility | Own provisioning | Peer comparison |
| --- | --- | --- |
| Native resolution/install | Retain portable upstream URL/hash/layout data and one bounded generic installer. | Mise/Aqua reuse backend/registry recipes but retain portable Bazel export data/adapters; Nix realizes packages/closures and separately exports portable artifacts. |
| Python consumer | Generate ordinary owner-bound dependency wheels; uv resolves direct requirements. | Same consumer mechanism is common work, not a manager advantage. |
| Selections and direct identities | Existing environment map, generated registrations/inventory, selected direct links. | SCORE retains selection/command compatibility policy in every candidate. |
| Update safety/state | Immutable prepared trees, completion markers, prefix lock, safe additive links; no ownership ledger or uninstall lifecycle. | Peer ledgers/profile removal are useful optional behavior, not required parity under the corrected scope. |
| Runtime ownership | Ubuntu/APT/features plus uv Python environments and upstream runtime archives. | Mise/Aqua retain corresponding trees/environments; Nix additionally operates store closure production/transfer/activation. |
| New transformations | Existing owners directly feed native installation and Bazel; one ordinary Python metadata export. | External native owners require portable Bazel metadata export; all require dependency release binding/checks. |

This does not prove an overall lifetime cost winner. External recipes can
remove upstream asset discovery/layout work, but do not erase portable Bazel
metadata, selections, release packaging, providers or compatibility tests.
Conversely the own option retains downloader/archive maintenance and platform
asset review rather than transferring them to a manager ecosystem. Compare
those concrete duties, not raw code size, prototype time or invented hours.

## Evidence and remaining coverage

See [the compact evidence archive](../experiments/tool-manager-comparison/own-evidence/README.md)
for exact checks, integration results, source boundaries and remaining gaps.
The peer M6/M7/M8 claims remain tied to their archived sources; this report
does not relabel peer execution as an own pass.

**Matched in executed amd64 evidence:** maintained A/B dependency releases and
stale rejection; uv/uvx release-only updates; same-prefix native updates;
public Bazel Ruff behavior; generic Node post-create/non-root terminal/hooks/
DinD/Buildx; all current selected direct commands; and a **fresh complete
no-cache published-image build with the unchanged feature suite**, using
production artifact URLs and no mirror. Its 79 assertions passed as vscode
inside the build; the cache-only output was not loaded, launched or published.
The prior cached-provider suite separately passed 81 assertions; environment
variable assertions make these totals context-dependent, not a fixed threshold.
Existing final-source checks passed 45 unit regressions and both Bazel shell
tests. Offline,
read-only uid-1000 checks cover all 16 exposed identities (14 selections plus
two Python aliases), 16 direct/strict comparisons, two behavior checks, three
language-server exchanges and the bounded Bazelisk launcher guard.
The existing public Bazel pre-commit target also actually ran version 4.7.0.

**ARM64 prepared execution also passed under QEMU:** the same 14 selections/
16 exposed identities were newly prepared from current owners using original
URLs on the retained final-arm64 OS substrate. Offline/read-only uid-1000 checks
passed the same 16 direct/strict comparisons, two behavior checks, three LSP
exchanges and guarded Bazelisk execution. All exposed commands resolve into the
new prefix; the 11 native commands, Python interpreter and basedpyright's bundled
Node were independently checked as AArch64 ELF. This is not native ARM hardware,
nor a full-image claim from a cached substrate.

**Remaining boundaries:** a separate fresh full ARM64 attempt completed both
local feature install stages and reached the unchanged test suite, but the
task's 30-minute cap interrupted pycairo's source-build dependency installation.
Its selected s-core-local verification passed; the remaining suite/build did
not complete. Three reported artifact retries recovered on production URLs.
This is an incomplete bounded QEMU attempt, not a full-image pass, a source
defect, a disk failure or proof that a longer run cannot succeed.
A second fresh attempt allowed 45 minutes but failed earlier when the preserved
Bazelisk provider's download of Bazel 8.6.0 ARM64 was reset by the peer.
That retry did not hit its cap or reach the suite. Both records remain separate;
neither is a complete ARM image pass. This provider acquisition failure is not
silently attributed to the shared native artifact engine or bypassed with a
mirror. It illustrates a retained provider boundary that a comparison must
identify separately from selected-tool provisioning.
A targeted follow-up with the newly prepared ARM64 Bazelisk then downloaded and
ran the real Bazel 8.6.0 in an isolated uid-1000 cache, and ran it again offline
from that cache. This diagnoses the image failure as transient acquisition,
not an unsupported engine/platform; it does not complete the image or suite.
Native ARM hardware, native Mac hardware, hosted release distribution
and long-term retention remain open. The peers' later additional
codespell selection is not added to this baseline's preserved inventory.
Peer-native offline repair/store verification and automatic host deselection
are optional differences, not missing requirements under the user correction.

The Node gate ultimately passed on final source; task-only terminal retries
retain the same assertions while tolerating transient nested BuildKit registry
resets. A full cached-substrate preparation and current feature suite also
passed, using a checksum-identical public OpenCode archive mirror after three
container download timeouts. That historical task catalog changed transport
only; production owners are untouched. The later fresh amd64 build and ARM64
preparation succeeded on production URLs without overrides. Online acquisition
and offline prepared execution are reported separately.

The original disk-cancelled amd64 attempt (1.21 GiB free before local features)
remains a failure record. The parent explicitly authorized removing obsolete
comparison images, restoring about 42 GiB; sources, snapshots, evidence, retained
final substrates and running containers were preserved. The fresh retry closed
that resource-blocked gap, rather than relabeling cached-provider execution.

**Repairs found by execution:** grouping shared-archive commands preserves
uvx's adjacent uv dependency; stable uv tool environments expose the language
server and pytest aliases; provisioning now defaults to its actual interpreter
rather than accidentally selecting a host-managed interpreter; reported,
bounded download retries handle transient acquisition failures. Focused tests
protect checksum failure/no publication, unsafe archive members, untracked or
user-replaced command conflicts, repeat updates, generated removal and exact
wheel dependency binding. The pre-existing archive-member refresh fix remains
inherited work, not a newly invented own-option result.

This closes the maintained amd64 release/consumer/provisioning comparison gap
without another native version owner/export lifecycle. The fresh amd64 provider
gate and ARM64 prepared-tool gate now also pass. This does **not** establish
native hardware/macOS or public-distribution parity, or total lifecycle cost
superiority over an ecosystem manager.

The prepared launch checks poison manager/Bazel paths and compare actual direct
and strict outputs/statuses. Language-server checks are a separate boundary:
Starpls naturally calls `bazel info execution_root output_base release
starlark-semantics workspace` to inspect its workspace. That is tool functionality,
not resolving or launching Starpls through Bazel. The LSP check uses normal
provider PATH and refuses Bazel fallback downloads; initialize/shutdown is not
proof of full downstream Bazel workspace semantics.
