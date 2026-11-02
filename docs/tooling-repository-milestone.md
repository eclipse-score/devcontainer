<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Repository integration: mise, aqua and Nix

Milestone 2 moves all three candidates beyond the
[three-tool reference](tooling-reference-milestone.md). Each candidate now
supplies the existing repository toolchain through real root metadata, existing
Bazel labels and locally built Ubuntu tooling images. No candidate is selected
and nothing is published. This scope is not a measured percentage of the whole
repository migration.

## What actually moved

| Area | Result in each candidate worktree |
| --- | --- |
| Repository tool selection | actionlint, bazelisk, buildifier, Ruff, ShellCheck, uv, uvx, yamlfmt and pre-commit are selected by native configurations. uv/uvx share one release decision. |
| Python delivery relevant to #189 | The broader published tooling selection adds pytest and basedpyright. Standard package extras expose Ruff and all three Python distributions to normal uv/uvx consumers. |
| Existing native compatibility metadata | Seven real `tools/lockfiles/*.lock.json` files are generated from candidate-owned selections and resolved artifact data. Existing root MODULE/BUILD labels consume them. |
| Existing Python compatibility metadata | `tools/score_tools/python_tools.bzl` receives generated versions while retaining public command identities and descriptions. |
| Existing repository setup | Native/Python fields of `tools/environments.json/repository` are generated from native selections; npm and unrelated environments remain separate. |
| Update ownership | The old direct Renovate uv pin rule is removed. uv's Bazel helper now follows the native uv owner. Full candidate-native update automation remains integration work. |
| Runtime installation | Both tooling profiles have real locally built images with release files copied/provisioned into the image. Runtime tools do not rely on producer-cache mounts. |
| Consumer behavior | Existing root Bazel targets, actual `tools/run-tool` modes and selected real pre-commit hooks are exercised. |

These are modifications to actual checkout consumers in each existing worktree,
alongside the maintained candidate producer under `experiments/`. The generated
snapshots preserve existing interfaces and keep unmigrated tools available.
The primary checkout records comparison evidence; adopting one of the three
worktree implementations remains a separate architectural decision.

## Common baseline acceptance

The [shared contract](../experiments/tool-manager-comparison/repository-milestone.md)
and [external runtime check](../experiments/tool-manager-comparison/repository-runtime-check.py)
define the scope. 🟢 means observed within this scope; cells are not scores.

| Observable criterion | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Real root Bazel targets: eight native commands plus pre-commit | 🟢 | 🟢 | 🟢 |
| Two COPY-built tooling images, uid12345, network denied | 🟢 | 🟢 | 🟢 |
| Selected versions through both existing container run-tool modes | 🟢 | 🟢 | 🟢 |
| Standard uv project and actual uvx for all four applicable distributions | 🟢 | 🟢 | 🟢 |
| pytest executes a test; basedpyright diagnoses a real assignment error | 🟢 | 🟢 | 🟢 |
| Six existing hook IDs on representative real repository files | 🟢 | 🟢 | 🟢 |

The hook checks cover Ruff format/check, ShellCheck, yamlfmt, buildifier and
actionlint using the existing pre-commit configuration. This is not a complete
remote CI run or an all-files sweep of historical experiment fixtures. Candidate
reports record exact commands, versions, network conditions and bzlmod checks.

## Independent update and final local selections

All three reject stale root/package metadata after a Ruff owner change and
exercise regenerated root targets plus ordinary uv/uvx dependencies. They also
reject an old prepared release against current native inputs. Existing releases
are not silently relabeled with new versions.

| Concrete update evidence | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Native Ruff selection changed | 0.11.13 → 0.11.12 | 0.11.13 → 0.11.12 | 0.17.2 → 0.14.6 |
| Regenerated root target and resolved Python dependency executed | Yes | Yes | Yes |
| Both updated tooling images also executed offline | Yes | Yes | Not repeated; both baseline images were tested |
| Current default Ruff selection after the probe | 0.11.13 restored | 0.11.12 retained as native owner | 0.17.2 restored |

The update versions are deliberate fixtures, not proposed production downgrades.
The Nix update additionally builds/observes the native selection; its root/uv
update evidence does not claim a second pair of tested images. Different proof
depths are explicit and are not treated as manager capability differences.

Other final local Python selections are pre-commit 4.7.0 in all three;
pytest 9.0.2 / basedpyright 1.35.0 in mise and aqua, and pytest 9.1.1 /
basedpyright 1.39.8 in Nix. Native and Bazel uv/uvx agree within each candidate:
0.13.6 for mise/aqua and 0.13.5 for Nix. Package versions follow the tested native
owners; this comparison does not claim identical versions across candidates.

## What the larger implementation exposed

- **Bazelisk is only part of a prepared Bazel runtime.** Images must prepare the
  selected Bazel and embedded runtime online as the eventual user. Bazelisk
  ignored `.bazelversion` in a directory without a recognized workspace marker;
  the image/check fixtures now establish that workspace or explicitly derive
  selection from the existing version file. No second Bazel pin is introduced.
- **The Bazel helper must join the version ownership migration.** Retaining its
  old uv lock as an independent authored pin would leave two update paths. It is
  now generated from the same uv selection as native delivery.
- **An old release can be internally consistent and still stale.** Drift checks
  must compare current native inputs with generated compatibility/package data,
  rather than only comparing an old release with old root files. Prepared native
  releases must be rebuilt, not relabeled by changing their metadata in place.
- **More tools exercise more delivery shapes.** The adapters now handle raw
  executables as well as archives and shared uv/uvx artifacts. Multitool rejects
  extra comment properties in its lock JSON, so provenance belongs in supported
  metadata or adjacent documentation.
- **Nix input boundaries matter during iteration.** A path flake rooted above
  large generated closures also copied those outputs into its source. The native
  flake inputs now live in a separate small directory, using the normal Nix path
  mechanism rather than adding a custom source-filter framework.

These findings were exchanged while implementing the candidates. The shared
runtime tests also avoid treating exact formatter layout as an architectural
requirement. New obstacles and fixes do not by themselves establish a manager
ranking.

An [independent codex-1 CLI review](../experiments/tool-manager-comparison/repository-cli-review.md)
found no definite implementation bug. It identified a remaining freshness limit:
mise/aqua prepared-release guards do not uniformly bind artifact-only checksum
refreshes at unchanged versions. The tested contract covers declared-version
changes; stronger same-version artifact-refresh binding remains separate work.
Earlier README inconsistencies cited during the review are superseded by the
finished milestone-two reports.

## Remaining work and comparison limits

All three still require the integration classes identified in the
[reference responsibility table](tooling-reference-milestone.md): applicable
native/Python identity mapping, compatibility export, runtime handoff and release
binding. mise coordinates backends through native configuration environments;
aqua/uv coordinates native tags and Python dependency groups; Nix preserves
package selections and store closures. Nix additionally resolves portable
upstream artifacts for the simple Bazel path. Adding tools has made those
responsibilities concrete; it has not measured whole-migration engineering hours.

At this checkpoint, the Node/Docker outer development container and the full
published S-CORE image with its APT packages, features, LLVM/Rust and CodeQL
had not been migrated. The subsequent [production milestone](tooling-production-milestone.md)
addresses prepared-tool integration into that full image.
The local `published` tooling profile is the broader tested tool selection, not
a claim to reproduce that complete image. Other native tools, final source
layout/API, all-platform execution, complete update automation, release hosting,
archival and remote CI remain open. Existing Python bootstrap/source-build limits
from milestone 1 remain relevant to the lightweight Bazel adapter.

Each sibling worktree's `experiments/tool-manager-*/reference/README.md` documents
reproduction and bounded evidence. No worktree or image is published.
