<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M6: compare the completed tool-manager integration boundary

**Status, 2026-11-02:** all three candidate source audits confirm that the old
SCORE native installation engine and its `install` / `install-python` commands
are removed, with no production references into `experiments/`. The six latest
root integration results passed: three generic Node lifecycle gates and three
fresh amd64 builds with the existing feature suite. The published builds used
cache-only output; no resulting image was loaded or launched. No manager is
selected.

M6 keeps the public tool interface and removes SCORE's parallel native-tool
installer. All candidates now generate an ordinary Python dependency wheel
from maintained `tools/` owners and consume it with normal `uv` / `uvx` commands.
The release version is explicit and package identity is configurable; a package
name may have a default, so supplying a name is not a universal required input.
Existing direct tool commands, Bazel labels and fallback, and prepared command
behavior remain. Prepared invocation does not require a manager or Bazel.

The manager boundary determines who resolves and delivers tool payloads. SCORE
continues to own the shared selection, exposed-command safety, public Bazel
compatibility, and release-package contract. The day-to-day manager work differs
by mechanism: Mise has fewer local recipe exceptions for the current inventory;
Aqua combines registry recipes with uv and retains APM's adjacent runtime tree;
Nix supplies package closures and profile membership replacement, with its
store and host lifecycle to operate. These observations describe current
responsibilities, not total effort or a preference.

## Responsibility comparison

Legend: 🟢 the manager or its normal ecosystem supplies the core mechanism for
the row; 🟡 SCORE still owns an adapter or shared policy at that boundary; 🔴
the candidate adds a distinct ongoing runtime lifecycle. Colors are categorical
responsibility markers, not quality or cost scores.

| Maintained responsibility | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Resolve selected tool packages | 🟢 Current inventory uses mise backends with fewer local recipe exceptions. | 🟢 Aqua registry recipes resolve native tools; uv resolves Python packages. APM also needs its adjacent runtime tree retained. | 🟢 Nix packages and closures cover the current inventory, including a local OpenCode derivation. |
| Map selections to direct command identities | 🟡 SCORE maps owners and entrypoints to exposed links; mise owns backend resolution. | 🟡 SCORE maps selected Aqua commands and uv entrypoints to the public command surface. | 🟡 SCORE maps selected profile contents to the existing direct-command contract. |
| Retire deselected commands safely | 🟡 SCORE ledger reconciles per-environment links, preserves other owners and user replacements, and rejects unsupported untracked names. | 🟡 SCORE ledger reconciles per-profile exposures, preserves other owners and user replacements, rejects unsupported prefixes, and promotes only selected Aqua outputs. | 🟢 Native profile replacement removed Buildifier, added Starpls, and retained Ruff in the real profile check. Old store objects may remain until garbage collection. |
| Preserve the public Bazel artifact contract | 🟡 SCORE refresh maps maintained owners to portable URLs, hashes, and archive layouts. | 🟡 SCORE export adapts registry resolution to the existing portable artifact records. | 🟡 SCORE maintains separate portable artifact definitions; Nix store paths are not a substitute for those records. |
| Build and consume the ordinary dependency package | 🟡 Shared SCORE packaging contract and owner adapter; local wheels were consumed through uv and uvx. | 🟡 Same shared contract and owner adapter; local wheels were consumed through uv and uvx. | 🟡 Same shared contract, bound to Nix release metadata; local wheels were consumed through uv and uvx. |
| Keep public feature and invocation behavior | 🟡 Shared SCORE policy preserves existing features, direct commands, uv/uvx use, Bazel labels/fallback, and manager-free prepared invocation. | 🟡 Same shared policy. | 🟡 Same shared policy. |
| Operate runtime delivery and activation | 🟡 Manager install trees plus SCORE's environment ownership and direct-link reconciliation. | 🟡 Aqua trees, uv environments, selected-output exposure, and APM runtime-tree retention. | 🔴 Store-closure production and transfer, profile activation, and host lifecycle remain a distinct operating model. |

Aqua's selected-output rule is SCORE's direct-command compatibility policy,
implemented through Aqua's available API. It is not a general product inability
to expose aliases or transitive tools. Likewise, the shared Bazel exporter is
separate from manager-native package resolution.

The old SCORE-owned engine and its install commands no longer provide native
tool downloads. The remaining `install.py` applies selected APT/npm providers
and exposes environment/feature metadata and selection queries. The M5-specific state adoption and recovery paths were
removed. Mise and Aqua fail closed when selected commands collide with an
unsupported untracked prefix; begin with a fresh bin directory or prefix.

## Shared packaging and ongoing work

Package generation and release checks now live under maintained `tools/`
paths. Each candidate derives extras from its selected owners, builds a local
ordinary wheel, checks it, and exercises regular uv resolution and uvx
consumption. Local checks supplied candidate package identities; that demonstrates
a configurable identity, not a required package-name CLI argument. Nothing was
published. The public package identity, release hosting, and hosted release
process remain undecided.

| Candidate | One-time M6 integration work | Recurring maintained responsibility |
| --- | --- | --- |
| mise | Add shared-bin ownership and safe deselection; move package generation/checks under `tools/`; fix the clean PyPI-backend path by resolving the pinned nested uv executable and setting `MISE_PYPI_UVX=true`. | Update direct owners and lock/compatibility exports; reconcile environment membership during provisioning; supply the release version and configurable package identity. |
| aqua + uv | Add profile ownership/reconciliation; move package generation/checks under `tools/`; install distro Python before bootstrap; align the node user and tool PATH; promote only selected Aqua output after a real `gh` exposure failure; correct direct helper executable modes. | Refresh Aqua owner/checksum outputs and compatibility exports; reconcile selected commands; retain APM's adjacent runtime tree; supply the release version and configurable package identity. |
| Nix | Use native profile replacement; move package generation/checks under `tools/`; bind and validate release metadata without duplicating the retained store payload. | Update the flake and lock, refresh portable compatibility output, and maintain closure production, transfer, activation, and host/profile lifecycle. |

The Aqua bootstrap addition was bounded to installing distro `python3` before
the Python bootstrap runs. Its cached-base check started the bootstrap and
provider commands without building an image or provisioning tool payloads. The
Aqua source executable-mode and selected-command exposure corrections are
recorded separately from manager responsibilities in the evidence archive.

## Integration evidence

All six latest actual result records passed. Failed and interrupted attempts are
retained as historical evidence and are not counted as passes.

| Candidate | Root generic Node lifecycle | Fresh published amd64 build and feature suite |
| --- | --- | --- |
| mise | Passed, including the later interactive terminal check after the nested-uv fix. | Passed on the fresh retry. |
| aqua + uv | Passed, including terminal resolution for the configured node user and prefix. | Passed on the fresh retry after the executable-mode and selected-output fixes. The original unqualified `gh --version` compatibility assertion remains unchanged and passed. |
| Nix | Passed, including the interactive terminal check. | Passed on the fresh retry after correcting the test-shell environment. |

The lifecycle gates ran the generic Node Dev Container `up` / post-create path
and a later interactive terminal check. The published gates ran fresh amd64
builds with the existing complete feature test suite appended and executed as
`vscode` in a login shell with passwd-derived HOME. The shell loads the feature's
real profile setup, including `JAVA_HOME`; the harness did not inject that
variable or weaken assertions. Aqua's existing unqualified GitHub CLI version
assertion was retained and passed. All three builds used cache-only output, so
no built image was loaded or launched.

Separate prepared-command checks ran five direct-versus-strict cases per
candidate under poisoned PATH, including Ruff's expected nonzero exit and a
filename containing spaces. All actual tools ran, direct and strict results
matched, and no manager/Bazel interception marker fired. Nix used a validated
M6 store read-only in the cached audit image with network disabled and user
1000; this does not establish host bootstrap or full-image behavior. The
individual records and runtime context are archived.

Aqua's actual same-prefix Aqua 2.65.2 + uv 0.13.6 reprovision retired owned
Buildifier and preserved a user-replaced deselected actionlint plus an unrelated
sentinel; retained pinned repository commands ran. Cross-profile sharing,
Python alias retirement, and additional symlink cases remain fixture-only. A
separate Nix consumer check used an ordinary local wheel through uv and uvx
without Nix runtime involvement.

The latest source audits and maintained-source inventory, worker handoffs,
source-fix summaries, six passing results, historical failure results, and
prepared-runtime checks are indexed in the [M6 evidence archive](../experiments/tool-manager-comparison/integration-evidence/README.md).
No raw logs, built runtime payloads, or release contexts are included.

### Boundaries and historical evidence

The result records distinguish earlier problems and their resolution. Mise's
first lifecycle attempt found the nested uv executable issue; a subsequent
attempt was interrupted before a result; the later corrected lifecycle passed.
Aqua's first lifecycle reached post-create but its later terminal lacked the
configured node prefix; the corrected retry passed. The first Nix lifecycle
attempt was manually interrupted after oversized generated reference outputs
were noticed. About 5 GiB remained, above the 4 GiB automatic start floor, so
the disk safeguard had not fired; a later lifecycle result passed.

The initial Nix published feature run failed because its non-login harness shell
did not load the feature's real `JAVA_HOME` profile. The retry used a login
shell and passed the unchanged suite. The first Mise published attempt failed
before candidate build because the temporary harness image name had uppercase
characters. Aqua's published attempts recorded a real direct-script executable
mode failure, followed by a real `gh` exposure failure; Aqua corrected helper
modes and staged/promoted selected outputs, then the unchanged suite passed.
These earlier result records remain in the archive, separate from the latest
passing results.

ARM Linux and macOS execution were not run. No hosted release or adoption was
performed. The managerless control has not implemented M6's maintained package
generation, deselection behavior, and equivalent local-wheel flow. This
comparison therefore cannot establish equivalent control maturity or prove
that managers are cheaper.

The M5 comparison's recommendation hypothesis is historical. M6 supports only
the narrow current-inventory observation that Mise needs fewer local recipe
exceptions and demonstrates Nix's profile/closure capabilities. It does not
establish total lifetime cost, general maintainability, or a production
preference. No adoption is declared.
