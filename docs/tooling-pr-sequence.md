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

# Proposed PR sequence from the local reference

This local breakdown derives from the complete, validated
[reference](tooling-reference-implementation.md). It specifies review outcomes
and dependencies; no PRs have been created. The discovery commits are deliberately
not the proposed PR boundaries.

## Dependency order and resulting behavior

| PR | Outcome | Depends on |
| --- | --- | --- |
| 1. Share the catalog reader | Catalog consumers do not import container installation code; the Python definition has one portable owner | Baseline |
| 2. Declare native selections | Features and repository setup install native tools from shared membership; native registrations and release updates cannot silently drift | 1 |
| 3. Consolidate Python CLI delivery | pre-commit, basedpyright and pytest share package definitions, Bazel targets and a system-wide container policy | 1, 2 |
| 4. Own remaining feature version policies | APT constraints, release metadata and compatibility expectations replace feature YAML; shell setup uses a quoted data bridge | 3 |
| 5. Apply provider compositions | APT, temporary build dependencies and special setup follow declared selections; actual installations are checked as the development user | 2, 4 |
| 6. Generate the complete inventory | Every managed provider, bundle and helper has discoverable ownership, policy, platforms and delivery; drift checks and update documentation follow the final sources | 2–5 |
| 7. Deliver Python tools through standalone uv (#189) | A Git-selected package carries the shared Python definitions and runs tools without Bazel or container installation code | 3, 6 |

Land in this order to keep each state usable. #189 was implemented and exercised
with the foundation during local development; its later position is a review and
landing dependency, not a decision to defer validating that use case.

## 1. Share the catalog reader

Move literal catalog parsing and native metadata access into `score_tools.catalog`.
Put the literal Python definition in `score_tools/python_tools.bzl` and retain the
old exported Bazel label as a forwarding file. Adapt the container installer,
README generator and Bazel loading together. This PR keeps the Python catalog
limited to the existing pre-commit entry and preserves installation selections.

The resulting repository still installs and runs the same tools. There is no
standalone console script or packaging interface yet.

Validation: existing pre-commit hooks, both Bazel contract tests, generated-table
synchronization and `bazel run //tools:pre-commit -- --version`.

## 2. Declare native selections

Introduce the native portions of `environments.json`, an environment-native
installation command and checks of explicit multitool hubs/aliases against the
native catalog. Convert both features and the repository post-create script to
those selections. Keep their existing Python installation calls until PR 3;
there must be no interval when pre-commit is missing or installed twice.

Remove the unused apm/opencode YAML values and their duplicate Renovate managers.
Make native digest refresh derive sibling version copies from the basename owner,
handle version-bearing asset filenames, and fail on missing hashes. Keep the
existing native versions and artifact layouts.

Validation: native registration/selection drift tests, release-refresh tests,
existing Bazel contracts, native target invocation and image native-tool checks
for both architectures. The native selection change must not remove Python CLIs.

## 3. Consolidate Python CLI delivery

Add basedpyright and pytest to the same literal owner as pre-commit; remove their
old YAML pins. Derive Bazel Python targets from that dictionary. Add Python
membership to the environment selections and make the environment installer
install native uv before Python distributions. Remove the superseded explicit
pre-commit calls and home-directory-based uv installation commands together.

All three tools remain available to the development user from system paths.
Container and Bazel delivery select the same distribution/version/entrypoint;
Bazel continues to require no host Python. There is still no standalone uv
package in this intermediate state.

Validation: fake-uv launcher/installer contracts including cwd and failure status,
real pre-commit in Bazel and both images, basedpyright/pytest as the development
user, and the minimal image test with no system Python.

## 4. Own remaining feature version policies

Replace the remaining feature YAML version data with `providers.json`. Distinguish
APT install prefixes from distribution-following packages and independent Git,
Git LFS, gh and LLVM compatibility expectations. Keep CodeQL bundle/pack and
Bazel/preinstalled-workspace decisions distinct. Add stable references to
external configs and locks without copying their requested feature tags/options.

Replace yq bootstrap with the stdlib reader and quoted shell metadata. Adapt all
remaining setup and tests in the same PR so no deleted YAML path remains live.
APT installation can still be the existing feature shell commands at this point;
they read version variables from the new owner. Add package/composition details
in PR 5 rather than introducing unused installers here.

Validation: metadata quoting/restricted-catalog tests, comparison of all migrated
values with the baseline, compatibility checks and affected image builds/tests on
both architectures. No independent pin or additional parser is introduced.

## 5. Apply provider compositions

Add provider package requests and the APT/build/setup/npm portions of environment
membership. Convert handwritten APT lists and cleanup to those selections.
Preserve normal APT recommendations, QEMU's explicit exception, Debian epochs,
Python build support, system paths and the Dev Containers remote user.

CodeQL pack membership is owned once by its bundle and read by download and
verification. Java/CodeQL/Bazel setup and functional checks query environment
membership. Reject undefined tools, provider mismatches, missing dependencies,
unsupported platforms and unknown APT policies before changing packages; declared
Linux arm64 CodeQL omissions remain explicit.

Add installed-result verification: command access and reported versions,
Debian installed state/constraints, Python modules, npm resolution and removal of
temporary packages. Keep feature-specific functional checks for Java setup,
CodeQL packs, pycairo builds and preinstalled Bazel.

Validation: selection removal/platform/preflight and installed-drift tests;
full published-image and repository-environment builds/tests on both architectures
as non-root users. Run existing trust-store checks as well.

## 6. Generate the complete inventory

Expand README generation to native, Python, APT, special release, feature, image,
fixture and helper definitions. Resolve feature requests and lock resolutions
from their existing native owners. Expose version-source links, actual update
ownership, environment membership, platform limits and delivery availability.
Include optional dive and make its install script consume its owned version and
hashes. Check the unavoidable proxy/default Dockerfile base registration.

Document how to add/update/remove a selection and the actual version guarantees.
Retain run-tool behavior and its tests, while removing the claim that arbitrary
container/PATH execution attests a catalog version. Wire final drift checks into
pre-commit and CI. Preserve existing public Bazel labels.

Validation: generated inventory `--check`, negative registration/selection and
update tests, runner contract tests, optional dive installation and repository
checks. This PR changes discoverability and drift detection, not tool versions.

## 7. Standalone uv delivery (#189)

Add `pyproject.toml`, package the literal Python definition and expose `score-tool`.
The console script chooses package/version/entrypoint from that owner and execs
caller-supplied uv. It does not import the container installer, duplicate pins or
bootstrap its own uv. Document the Git-release consumer command and the migration
from unpinned `uvx pre-commit` calls.

Add the local-Git smoke test and CI invocation. It installs outside the checkout,
asserts packaged catalog presence, runs real pre-commit, then checks argument
boundaries, cwd and returned failure status through the installed console script.

Validation: `tools/tests/git_delivery_smoke.sh` against the PR commit, console
boundary tests, real Bazel/container/uv pre-commit selection and the no-host-Python
Bazel test. No publication is necessary for any of these gates.

## Assembly and review rules

For each PR, copy the outcome's hunks from the working reference and adapt tests
and docs to that intermediate interface. Do not cherry-pick the broad WIP
commits as if they were reviewable PRs. Keep old callers until their replacement
lands in the same PR. Each row names the working behavior that must remain and
the validation gate required before proposing that PR.

The runtime, CI and maintainer documentation changes together lead to the full
reference. Local goal instructions, validation diaries and this planning document
are review aids; decide their upstream documentation placement separately if
publication is later authorized. No upstream changes are authorized by this plan.
