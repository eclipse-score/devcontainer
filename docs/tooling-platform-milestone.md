<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M7: Linux ARM64 platform comparison

**Status, 2026-11-02:** all three candidate worker runs prepared the maintained
`published` selection for Linux ARM64 and completed their non-root, offline
runtime checks under QEMU. Independent root review now establishes the same
15 selected command identities for all three: 14 ordinary version/behavior
checks plus guarded ARM Bazelisk execution. Aqua also tested its two additional
exposed aliases, bringing its coverage to 17 identities. The same five root
direct/strict cases passed per candidate (15 comparisons). No manager is selected.

This extends the M6 amd64 integration comparison to real ARM64 executables.
The [shared M7 contract](../experiments/tool-manager-comparison/platform-milestone.md)
requires fresh owner-selected output, paths and versions from that output, and
behavioral checks without relying on the old tools in the substrate image. All
three candidates met that preparation boundary. The common maintained union is
15 tool selections: actionlint, apm, basedpyright, bazelisk, buildifier,
codespell, opencode, pre-commit, pytest, ruff, shellcheck, starpls, uv, uvx,
and yamlfmt. Aqua also exposes the `basedpyright-langserver` and `py.test`
entrypoints, so its prefix contains 17 command identities.

The host was x86_64. The cached image
`sha256:b36448960057f54745f841561338487c5e9e2128526113c24b4861a7cf0f065a`
served only as an Ubuntu/Python ARM64 OS substrate; QEMU ran the ARM64 tools.
Successful runtime checks used uid 1000 and no network. They resolved to a
fresh Mise prefix, Aqua prefix, or Nix store profile, rather than the image's
pre-existing tools. This is emulated execution, not native ARM performance or
hardware evidence. It is not a full ARM Dev Container feature-image build, and
macOS ARM was inspected only as configuration/metadata.

## Acceptance results

“Executed” counts selected command identities actually invoked, not preparation
or presence in a manifest. Each detailed result records exact paths, versions,
checksums where captured, commands, and runtime conditions.

| M7 evidence | Mise | Aqua + uv | Nix |
| --- | --- | --- | --- |
| Fresh maintained `published` output | **Verified.** Fresh prefix; all 15 selected identities, including APM, have owner versions and prepared paths recorded. No old M5/M6 tool payload was reused. | **Verified.** Fresh ARM64 prefix matches all 17 selected command identities. Aqua's real `cp` output included transitive `gh` for uv, but the existing selected-only promotion kept `gh` out of the public prefix. | **Verified.** Fresh aarch64 release; published/repository bundles and all 181 store paths matched the current owner. Profile membership is the 15-command selection. |
| Non-root offline runtime | **Verified.** Runtime and wheel consumer ran as uid 1000, network disabled, read-only root. | **Verified.** Runtime ran as uid 1000, network disabled, `UV_OFFLINE=1`, and read-only prepared prefix. | **Verified.** Runtime ran as uid 1000, network disabled, read-only root/store and fixtures; `uname -m` reported `aarch64`. |
| Selected command checks | **15 common identities tested:** 14 ordinary version/behavior checks plus root's ARM Bazelisk guard. Prepared paths, versions and fingerprints are recorded. | **15 common identities plus two aliases tested:** ordinary checks, the root ARM Bazelisk guard, `py.test`, and basedpyright language-server initialize/shutdown. | **15 common identities tested:** 14 ordinary version/behavior checks plus root's ARM Bazelisk guard; the complete profile and closure were owner-checked. |
| Direct uv and uvx | **Verified:** uv/uvx 0.13.6; offline local-wheel `uv lock`, `uv sync`, and `uv run`, plus `uvx` with the wheel's Ruff extra. | **Verified:** selected uv/uvx 0.13.6; `uvx --offline` ran pytest from local cache. | **Verified:** uv/uvx 0.13.5; offline `uvx` ran Ruff using staged local wheels, without runtime network or index access. |
| Python and Ruff behavior | **Verified:** pytest, basedpyright, and offline pre-commit config checks; Ruff produced expected F821/exit 1 and codespell caught the fixture typo. | **Verified:** both pytest names passed a real test; basedpyright returned zero diagnostics and its LSP initialized/shut down; Ruff produced expected F401/exit 1. | **Verified:** pytest asserted Python 3.14 on aarch64; basedpyright had zero diagnostics and pre-commit config validated offline; Ruff produced expected F401/exit 1. |
| Common direct/strict cases | **5/5 passed:** uv, uvx, Ruff and pre-commit versions, plus Ruff F821/exit 1 with a spaced filename. Direct/strict results matched; poisoned PATH recorded no interception. | **5/5 passed:** the same cases and expected exits/outputs, from the prepared prefix with no manager/Bazel interception. | **5/5 passed:** the same cases and expected exits/outputs, from the Nix profile with no manager/Bazel interception. The worker also verified strict missing-tool exit 127. |
| Common Bazelisk guard | **Passed:** selected 1.27.0 ARM ELF (`e_machine=183`) executed as uid 1000, offline/read-only; expected fallback refusal/exit 1 before download or engine. | **Passed:** selected 1.27.0 ARM ELF (`e_machine=183`), identical conditions and expected refusal/exit 1 before download or engine. | **Passed:** selected 1.29.0 ARM ELF (`e_machine=183`), identical conditions and expected refusal/exit 1 before download or engine. |
| macOS ARM | Static config only: nine native lock records plus Starpls and the bootstrap have Darwin ARM URL/checksum data. Four Python tools use generic uv resolution. No macOS execution. | Static config only: checksummed Darwin ARM assets for ten native tools and Aqua bootstrap; local Starpls/APM registries declare Darwin ARM. Python requirements have no explicit OS allowlist. No macOS execution. | Static evaluation only: all 15 versions/profile lists remained; Nixpkgs metadata lists aarch64-darwin for 14/15 packages. OpenCode has no generic `meta.platforms` but selects an explicit Darwin ARM asset/hash. No macOS execution. |

Root's [common review](../experiments/tool-manager-comparison/platform-evidence/root-review.json)
adds the same guarded launcher test for every candidate, with
`USE_BAZEL_FALLBACK_VERSION=error:score-m7-no-engine`. The expected refusal
establishes ARM launcher execution before any download or Bazel engine run;
it does not establish standalone Bazelisk version reporting or engine behavior.
The earlier worker reports remain point-in-time evidence. Their present-only
or unverified Bazelisk findings are superseded at this common guard boundary
by the root results.

The five common cases compare normal direct tool calls with optional strict
`tools/run-tool` verification. Ordinary tool and uv/uvx use needs no wrapper.
The root JSON records exact paths, runner hashes, commands and equal
exit/stdout/stderr results, including the filename `bad input.py`. These checks
ran under ARM QEMU as uid 1000, offline with read-only prepared output and
poisoned PATH; no manager or Bazel interception occurred.

## Responsibility comparison

The markers classify the kind of ownership, not quality, cost, or a ranking:

- 🟢 **Manager-native mechanism:** the manager or its normal package ecosystem
  resolves, installs, or composes the selected tool.
- 🟡 **Shared SCORE policy/adapter:** SCORE still defines or preserves the same
  selection, direct command surface, safety, or compatibility contract.
- 🔴 **Recurring platform data/operation or unverified boundary:** explicit
  per-platform inputs, closure/runtime work, or additional execution evidence
  remain necessary. This is not a negative quality grade.

| Responsibility | Mise | Aqua + uv | Nix |
| --- | --- | --- | --- |
| Native tool resolution | 🟢 Existing mise backends and locked artifacts cover the current inventory; current owners need fewer local recipe exceptions than Aqua. This is an inventory observation, not a total-effort result. | 🟢 Aqua registry recipes and checksum records resolve native packages; APM and Starpls use local registries. | 🟢 Nixpkgs supplies ordinary packages; OpenCode is a local derivation with selected platform assets. |
| Python tool installation | 🟢 Mise's maintained uv/PyPI configuration installs the selected Python tools. | 🟢 uv resolves the Python group; `basedpyright` brought the ARM `nodejs-wheel-binaries` 24.19.0 runtime dependency. | 🟢 Python tools are part of the Nix profile/closure; M7's pytest used the selected Nix Python 3.14. |
| Public command selection | 🟡 SCORE selects environments and the copied-output allowlist, then maps owners to public links. | 🟡 SCORE's copied-output allowlist prevents transitive `gh` exposure; its command map includes two Python entrypoint aliases. Retaining APM's adjacent runtime tree is a layout adapter. | 🟡 SCORE chooses the Nix profile map and compatibility exports; Nix realizes that selected membership. This is distinct from a copied-output allowlist. |
| Native command removal | 🟡 SCORE reconciles its owned prefix commands against selection, protecting shared selections and user-owned files. | 🟡 SCORE reconciles its owned prefix commands and promotes only selected output, with shared-selection and user-file protection. | 🟢 Native profile replacement removes deselected command membership through Nix's manager mechanism, demonstrated in M6. SCORE still owns the desired profile selection. |
| Prepared direct/strict compatibility | 🟡 `tools/run-tool` preserves direct prepared calls and existing ordinary Bazel compatibility behavior. All successful prepared M7 calls avoided manager/Bazel fallback. | 🟡 Same shared contract; the two additional Python names are owner entrypoints, not new manager invocation requirements. | 🟡 Same shared contract; strict missing-tool handling returned 127 without Bazel. |
| Release package boundary | 🟡 Maintained SCORE packaging turns owner data into ordinary wheels consumed through uv/uvx. Release version is explicit and package identity is configurable; a name can have a default. Hosting and public identity remain undecided. | 🟡 Same maintained package boundary; Aqua provisioning remains an image/build-time task, not a requirement for wheel consumers. | 🟡 Same package boundary is generated from the Nix release manifest; it does not make Nix a mandatory prepared-call dependency. |
| Recurring platform work | 🔴 Check backend/bootstrap support and existing artifact URLs, checksums and archive layouts; supply missing data, then provision and execute a fresh target prefix. Python wheels rely on uv resolution. | 🔴 Check recipe/checksum and local-registry coverage, supply missing platform data, and resolve/test the uv runtime dependency graph. Selected-only exposure remains shared SCORE policy. | 🔴 Evaluate the target system/package metadata, supply missing custom assets/hashes, realize or substitute its closure, transfer it and test activation. Cross-producer observation handling is now implemented. |
| Present platform boundary | 🔴 macOS has declarations but no execution; generic Python resolution has no M7 macOS proof. | 🔴 macOS Python compatibility has no explicit per-OS allowlist or execution proof. | 🔴 OpenCode uses explicit Darwin asset/hash data without generic platform metadata; macOS was not run. |

Existing manager data may already cover a new platform; the recurring duty is
to verify availability and supply genuinely missing metadata, assets or runtime
dependencies. Corrected mount, cache and fixture failures were harness setup,
not evidence of a product capability gap or work that must recur on every
platform. Nix's cross-producer API repair is one completed source repair,
separate from producing and transferring each target closure. The current
Mise recipe observation does not establish lower total maintenance. The M7 evidence is
also not an equal M7 evaluation of a managerless control: it compares the three
maintained candidate delivery flows, without asserting a cost advantage over an
unimplemented control.

## Repairs and findings beyond a green version sweep

- **Mise:** no maintained source or pin changed for M7. The fresh run established
  that the current ARM lock/backends and wheel flow work. Root's common guard
  subsequently established the same bounded Bazelisk execution for all three
  candidates, without requiring an engine or standalone self-version query.
- **Aqua:** no maintained source or pin changed for M7. A real provisioning log
  exposed the extra `gh` file emitted while Aqua copied uv's dependencies; the
  existing selected-only promotion kept it private. `basedpyright`'s Python
  environment also resolved its bundled Node runtime dependency, and the real
  LSP exchange worked offline. These are concrete selection/runtime obligations
  hidden by a version-only check.
- **Nix:** M7 repaired cross-system release preparation. On an x86_64 Nix
  producer, target executables must not be run as if they had been observed on
  the producer. The updated `prepare.py` records deferred observations and
  requires explicit bounded aarch64-on-x86 emulation for profile assembly. The
  run matched both exported bundles and 181 store paths; 228 cache substitutes
  were needed, followed by four small derivations. This is a Nix producer and
  closure-operation responsibility, not a full runtime build.

The exact M7 source comparison and Nix regression boundary are in the
[archived source-change summary](../experiments/tool-manager-comparison/platform-evidence/source-change-summary.md).
The archive contains each compact worker result, handoff, candidate README, the
ARM substrate probe, the M7 start-source hashes, Nix macOS metadata, root's
independent source review, all three common guard results, all three common
runtime results, and [provenance hashes](../experiments/tool-manager-comparison/platform-evidence/provenance.json).
It excludes full runtime payloads and raw logs. Earlier setup failures and
Bazelisk attempts remain in unchanged worker reports; root's later common
checks define the current guard/parity result. Task containers may be removed
after checking: prepared prefixes, source and caches remain, but worker
`docker exec` reproduction examples may require recreating their containers.

## M6 and adoption boundary

The [M6 comparison](tooling-integration-milestone.md) records six amd64 root
gates passed against their recorded source hashes: three generic Node lifecycle
gates and three fresh amd64 build/feature-suite gates. Those results remain
historical for the M6 source snapshot. Mise and Aqua had no maintained-source
change in M7. Nix's M7 change passed seven focused unit tests, lint/format and
compile checks, plus this targeted amd64 regression:

```sh
python3 tools/internal/nix/sync.py --check \
  --release /tmp/score-m6-nix/release-amd64 --system x86_64-linux
```

It reported no stale outputs. The six root gates were not rerun against the
changed Nix preparation source; this document makes no such claim. No pins,
public identity, hosting choice, image publication, full ARM feature image,
native ARM run, or manager adoption decision is made by M7.
