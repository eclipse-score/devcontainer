<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Which approach removes work we would otherwise own?

**Historical M1–M4 ownership audit:** see the
[M5 comparison after actual installer removal](tooling-retirement-milestone.md)
for the later implementation. Retained-engine/handoff descriptions below are
evidence of the earlier state, rather than a permanent cost of each manager.

**Follow-up:** the [installer-retirement investigation](tooling-installer-retirement.md)
checks the actual remaining callers and package gaps. It supersedes the provisional
aqua preference below; the initial ownership audit remains supporting context.

**Assessment, 2026-11-01:** no new manager is needed for the standard Python
consumer package. The reason to adopt aqua or mise is to delegate native
installation recipes and artifact resolution. Nix additionally delegates runtime
dependencies, at the cost of a different producer/container package model.
The current implementations have not demonstrated a reduction in our maintained
installer surface: they retain it and introduce prepared-runtime handoff logic.

This is a source and ownership audit of the local implementations, plus a small
managerless control experiment. It is not an engineering-hours estimate or an
adoption decision. Earlier aqua preference is a hypothesis about a narrow final
architecture, not a measured advantage of its present prototype.

## Decision implications

1. **Keep the managerless consolidated reference as a serious baseline.**
   Python dependency delivery and direct execution do not justify a new manager.
   The baseline is this checkout's already consolidated reference, not untouched
   upstream; consolidation and release publication still cost work.
2. **Do not make Nix the default choice for the current scope.** Its distinctive
   benefit is runtime-closure ownership. Existing Ubuntu/APT/features and complex
   tools remain separate in these implementations. We would therefore add store
   deployment without replacing that existing operating model. This changes if
   runtime dependency ownership becomes a deliberate goal.
3. **Compare aqua and mise on native recipe ownership and actual deletion.**
   aqua has a narrow artifact-installation role; mise also coordinates backends
   and Python provisioning. The latter is useful only insofar as it replaces
   orchestration we would otherwise maintain. The current exporters and release
   work do not disappear under either candidate.
4. **Avoid adopting the complete experimental handoff architecture by default.**
   Compare a narrower final arrangement: manager provisioning inside the image
   build, generated existing Bazel metadata, and separately generated ordinary
   Python package metadata. This is an unimplemented alternative, not an already
   validated simplification. It may remove the need for cross-stage tool payload
   handoff, while retaining the real release/drift checks.

My present preference remains **aqua + uv for a narrow provisioning role**,
conditional on replacing our corresponding native installation responsibilities.
The observed missing-starpls case favors mise's generic GitHub backend and makes
this a close choice. There is no demonstrated large effort advantage between
those two. If either requires keeping every old path plus a permanent second
installation pipeline, the managerless baseline is the more convincing choice.

## The useful cost comparison

Costs below identify concrete responsibilities, not product scores. One-time
migration and repeated maintenance are separated; temporary probes are excluded.

| Responsibility | Consolidated baseline | aqua + uv | mise | Nix |
| --- | --- | --- | --- | --- |
| Native install recipe and release-layout maintenance | Ours in existing artifact metadata/installer | Delegate image installation to registry recipes; own missing recipes | Delegate to backends; generic GitHub backend handled starpls | Delegate to package definitions for available packages |
| Portable Bazel artifact metadata | Existing format is already authoritative | Still own archive/platform export mapping | Still own identity/archive export mapping; resolved lock already gives URLs/hashes | Still own upstream portable asset metadata separately from Nix derivation hashes |
| Python consumer extra generation | Add a small standard metadata exporter from existing pins | Same class of exporter from Python owner | Same class of exporter from mise owner | Same class of exporter from selected package versions |
| Python image environment | Existing uv install and runtime/path policy | Explicit uv provisioning and runtime/path policy | mise invokes backend preparation; preserve resulting install trees/runtime | Package includes its interpreter/libraries; preserve closure |
| Native version update | Update pin, refresh metadata, handle our layout assumptions | Update pin/checksums; own local-recipe changes | Update pin/native lock; own backend/export exceptions | Select matching package snapshot/input or maintain override if unavailable |
| Current container migration additions | No new prepared-runtime protocol required by baseline | Payload staging plus validated skip handoff | Install-tree staging plus validated skip handoff | Store closure transfer, command activation and validated skip handoff |
| Unmigrated APT, features, complex tools | Retain | Retain | Retain | Retain in current scope |
| Team operating model introduced | Existing JSON/Starlark/Python plus packaging/release work | Registry, policy/checksums and aqua bootstrap; uv remains separate | Backend/profile/lock policy and mise bootstrap | Nix language/inputs, package selection and store lifecycle |

The baseline's existing custom installer is a real obligation. A mature upstream
recipe ecosystem can reduce that obligation, but adopting a manager name does
not itself remove it. None of these alternatives automatically supplies our
SCORE release binding, public Python package hosting, downstream compatibility
or platform verification.

## What can actually be deleted?

The three worktrees share HEAD `2e337e4`; the source audit compares their current
installer changes against that common consolidated reference. Each adds a
prepared-tool branch, leaving the original download and extraction functions
present. Remaining `apm`/`opencode` paths and the explicitly preserved unprepared
starpls fallback still use native catalog installation. APT and complex feature
setup also remain. Python fallback installation is retained, even where the
prepared published selection skips all its Python commands.

| Existing responsibility | Actual status in all three prototypes | Removal condition |
| --- | --- | --- |
| `_cmd_install`, `_extract_member`, `_extract_dir`, checksum/download logic in `tools/internal/devcontainer/install.py` | Retained; prepared tools bypass it | Replace every remaining caller or keep a deliberately bounded fallback |
| `_cmd_install_python` in the same installer | Retained; prepared tools bypass it | Replace remaining unprepared Python installation contract |
| `tools/internal/refresh_lockfile_digests.py` | Retained; not removed by the candidate diffs | Migrate every authoritative native lock and its update automation; retain required compatibility output |
| Catalog validation, descriptions and feature membership | Retained/consumed by generated metadata | Still required; simplify duplicate decisions rather than assume removal |
| Bazel Python launcher and existing public labels | Retained | Compatibility obligation, not manager-specific waste |
| Python dependency package, release binding and drift checks | Added in each candidate | Required consumer/release work; also needed without a new manager |

This explains why the experiments look similarly complicated: **they combine
compatibility preservation, two installation routes and a producer-to-image
handoff**. The handoff has useful freshness/platform validation, but it is not
free and is not an inherent requirement of any candidate. Keeping all those
layers indefinitely would weaken the case for adoption.

A fair migration plan can retain fallback temporarily. Its claimed benefit must
then name the callers to migrate and the removal boundary; temporary coexistence
is not evidence that a manager can never reduce our code.

## Managerless control: Python delivery already works

The [reproducible probe](../experiments/tool-manager-comparison/managerless-probe.py)
reads the existing Python catalog and Ruff native pin, generates a data-only
setuptools package with ordinary extras, builds a wheel, and executes Ruff from
a normal consumer. It changes no production pins or packaging.

Observed in the [recorded proof](../experiments/tool-manager-comparison/effort-evidence/managerless-python.json):

- The generated extras carry the existing exact pins; no new manager or runner
  is included in the package.
- A consumer declares only the local facade's Ruff extra. Ordinary uv lock,
  sync and run select Ruff 0.11.13; `uv tool run --with` selects the same version.
- The installed `.venv/bin/ruff` runs directly and reports a real F821 undefined
  name diagnostic without calling a manager or Bazel.

Reproduce from the primary checkout:

```sh
python3 experiments/tool-manager-comparison/managerless-probe.py \
  --output /tmp/score-effort-control
```

Only the Ruff extra was executed; the other extras were inspected as metadata.
Host networking was allowed and existing caches could be reused. This is not
cold-install timing, offline verification, native-host provisioning, publication
or a fourth complete migration. It establishes that Python package delivery is
common integration work, not a deciding manager feature.

## Managerless maintenance also has concrete pitfalls

The existing refresh helper updates release tags, asset URLs and digests. A
controlled ShellCheck 0.10.0 to 0.11.0 edit with mocked upstream digests shows
that it leaves `file: shellcheck-v0.10.0/shellcheck` unchanged while generating
a 0.11.0 archive URL. The resulting extraction metadata is inconsistent.
The [fixture outcome](../experiments/tool-manager-comparison/effort-evidence/managerless-archive-update.json)
records the synthetic hashes explicitly; it is not a real release download or
a failure observed in a production image.

The baseline repair is now implemented: version-bearing `file` and `dir`
fields follow the release change. A regression test reproduced both failures
before the fix and passes afterwards; the existing missing-digest/no-write test
also passes. The recorded fixture is historical evidence of the discovered gap,
not the current behavior after this repair. This bounded fix does not handle
arbitrary future upstream layout changes.

That was a specific repair in our update helper, not proof that a manager
is mandatory. aqua/mise delegate the native installation layout to their
backends, but their portable Bazel exporters still carry layout assumptions and
need correct updates too. Nix's current exporter retains the existing artifact
recipe and refreshes version-bearing fields when its selected version changes.

## Which work would change the recommendation?

The next useful implementation boundary is **retiring native installer duties**,
not another all-green tool demonstration. For aqua and mise, identify the final
native installation path, migrate or explicitly exclude the remaining callers,
and show which fallback and refresh logic can then disappear. Compare that
result with retaining and fixing the consolidated baseline. Validate ordinary
updates and missing-registry additions against the same final boundary.

For Nix, further equal feature work is unlikely to justify its extra operating
model by itself. Its case needs an explicit benefit from runtime dependency
ownership, or evidence that maintaining our desired independent versions is
cheap enough to offset store/package-set management.

The [execution-path requirement](tooling-execution-paths.md) is a separate gate:
no approach is accepted if it forces slow per-call resolution or build analysis.
Startup overhead has not been measured here. No decision or publication follows
automatically from this assessment; all three worktrees are preserved.
