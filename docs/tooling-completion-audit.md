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

# Completion audit of the local reference

All ten [goal criteria](tooling-refactor-goal.md) were verified locally on
2026-10-30 against the complete reference. All changes remain on
`refactor/tool-management-reference`; no PR or publication exists for this
implementation. The limits below preserve the agreed scope and guarantees.

## Requirements and current proof

| Goal requirement | Evidence | Status |
| --- | --- | --- |
| Every managed tool/helper has owned source, policy, selection and platform/update information | Validated/generated inventory contains 63 definitions across native, Python, APT, release/setup, feature, image, fixture, npm and optional helper providers; `sync_readme.py --check` passes. Baseline coverage and intentional boundaries are described below | Proven |
| One version authority; shared installation membership; unavoidable registrations checked | Literal Python owner, native lockfile owners, provider definitions and environment selections; generated sibling release versions and native hub/alias checks; selection/removal/registration checks in the shared reader | Proven |
| Published and repository environments retain capabilities, including non-root and platform behavior | Final-source amd64 and arm64 S-CORE images built and passed all feature tests as vscode without tool/check overlays. Repository builds and derived installation/verification smoke images passed as node on both architectures; source comparisons match the current files | Proven |
| Native and Python Bazel delivery without host Python | Minimal Ubuntu image verifies neither python nor python3 is on PATH, runs real pre-commit 4.7.0 using uv-managed CPython, and separately runs native ShellCheck 0.10.0. Delivery-source hashes match the current launcher, Bazel macros, Python definitions and module configuration | Proven |
| Standalone uv from local Git, with packaged data and no Bazel/container installer dependency | `tools/tests/git_delivery_smoke.sh` passed at local code commit `e848cc4` outside the checkout; it checks the installed catalog and console script, real pre-commit, cwd, quoted/empty arguments and returned status. No source checkout or container installer is needed | Proven |
| Matching real Python package/version/entrypoint across three paths | Shared definition is pre-commit / 4.7.0 / pre-commit. Real Bazel, installed container and Git-selected uv executions report 4.7.0; launch/install argument contracts inspect the exact requirement and entrypoint | Proven |
| Generated docs, updates and meaningful drift checks use the final owners | README generation and check mode; Renovate derives native requests from lockfiles; digest refresh updates filenames/hashes and generated sibling versions or fails; tests reject selection, installed-version, package-state and process-boundary drift | Proven |
| Invocation/PATH/strict contract documented and tested; deliberate migration decision | `run_tool_test` verifies existing container/host/strict precedence and errors. `tools/README.md` and maintenance guide remove the PATH version-attestation claim and document explicit Bazel/uv choices; no downstream migration performed | Proven |
| Appropriate repository checks and affected image/delivery tests pass | 20 Python tests, both Bazel contract tests, repository hooks, final-source feature tests on both architectures, Git smoke and both repository-platform smoke images passed | Proven |
| Small PR breakdown with outcomes, dependencies, validation and working intermediate states | `tooling-pr-sequence.md` describes seven dependency-ordered PRs; keeps existing callers until replacements land together, identifies each usable intermediate state and its gate, and separates discovery commits from review boundaries | Proven: derived from the validated reference |

## Baseline coverage and version preservation

A read-only comparison against baseline commit
`0cc738794384cf32f08ba616c049bf8f3fb7124c` confirms:

- All 11 native command definitions, URLs, platform artifacts and checksums are
  byte-identical to the baseline native JSON files.
- All 37 explicitly requested APT packages in the S-CORE feature, including
  temporary build packages, match the new selection's resolved package names.
  Both features' native selections, the Bazel feature's temporary APT package
  and all four CodeQL pack members match their baseline install lists.
- All 23 feature-YAML version decisions retain their values in their new owners.
  basedpyright/pytest now use the Python literal; unused apm/opencode copies are
  removed in favor of their native owners; Git/Git LFS/gh values are explicitly
  independent compatibility expectations. Valgrind's request retains its epoch.
- The two Dev Containers configurations and locks, two published-image
  Dockerfiles, and workspace `.bazelversion` are unchanged. Feature and base-image
  version decisions therefore remain with their original owners.
- pre-commit 4.7.0, LLVM compatibility 20.1.8, the pycairo 1.29.0 fixture, optional
  dive 0.13.1 and its two hashes retain their values. The temporary yq bootstrap
  is deliberately removed because shared stdlib parsing replaces its function.

Native, APT, feature and Python guarantee levels remain different. The inventory
is an overview of explicitly selected tools and bundles, not a full dependency
closure: base/feature transitive packages, Bazel rule libraries, remote hook
implementation environments, editor extensions and CI-action dependencies retain
their own native manifests. They are not silently claimed to be individually
locked by this tool catalog. A formal SBOM and full environment locking remain
outside the agreed scope.

## Final-source image checks

Both `score-tooling-reference:final-amd64` and
`score-tooling-reference:final-arm64` built successfully from the final runtime
sources, including the Java selection guard in `e848cc4`. SHA256 comparisons
verify all 38 tracked tool/feature files in each image, including the catalog,
installer, provider/composition data, Bazel/Python/native definitions, metadata
bridge, feature installers and feature tests.

The full feature tests passed as vscode on each architecture with only the
test-project directory mounted read-only. There was no tool or feature-test
overlay. Checks cover actual command versions, APT package state/constraints,
Python CLIs, forced pycairo source compilation, Java setup, Bazel, trust stores
and temporary-package cleanup. amd64 additionally verifies CodeQL and all four
packs; the Linux arm64 omission is intentional and declared. ARM64 execution
uses binfmt emulation on amd64, not native ARM hardware.

The repository environment is built from its unchanged Dev Containers config on
both platforms. Derived smoke images copy the current tools, apply the repository
selection, switch to node, verify all selected commands/npm resolution, execute
Docker and Dev Containers CLI, and install a hook in a temporary Git repository.
The optional dive installer also passed artifact verification and execution in
disposable amd64 and arm64 development containers. Removing OpenJDK from a
disposable composition skips the actual Java setup block without querying javac
or changing the Java profile; the positive branch is covered by feature tests.

## Local image identifiers

| Image | Local identifier |
| --- | --- |
| `score-tooling-reference:final-amd64` | `sha256:b75f92cd2bd783d7ba6e377d1764757d489b0d4adb8bbf29379bd1e84d08a9a1` |
| `score-tooling-reference:final-arm64` | `sha256:b36448960057f54745f841561338487c5e9e2128526113c24b4861a7cf0f065a` |
| `score-tooling-repository-smoke:final-amd64` | `sha256:71cc45fa8b631c9dd7455467bcf833699c5568df5b3c38540130ac1dd9443f82` |
| `score-tooling-repository-smoke:final-arm64` | `sha256:0666856a64b2c198fe77a3a3a49dd3e4a7ee55712d199d3b71d413b3133b00ed` |

## Evidence locations for this local run

The reusable commands are in the maintenance guide, CI and
`tools/tests/git_delivery_smoke.sh`. Local execution evidence includes:

- `/tmp/score-baseline-policy-audit.json`: native, migrated policy and external
  configuration comparison against the baseline.
- `/tmp/score-baseline-composition-audit.json`: baseline APT/native membership
  and CodeQL pack comparison against the new provider/composition model.
- `/tmp/score-precommit-final.log`: repository hook checks.
- `/tmp/score-unit-final.log` and `/tmp/score-bazel-final.log`: 20 Python tests
  and both Bazel contract tests.
- `/tmp/score-tests-final-amd64.log` and `/tmp/score-tests-final-arm64.log`:
  all final-source feature tests.
- `/tmp/score-image-final-amd64.log` and `/tmp/score-image-final-arm64.log`:
  successful final-source builds.
- `/tmp/score-source-proof-final-amd64.json` and
  `/tmp/score-source-proof-final-arm64.json`: matching hashes of all 38 embedded
  tool/feature source files per image.
- `/tmp/score-repository-final-amd64.log` and
  `/tmp/score-repository-final-arm64.log`: repository environment installation,
  resolution, non-root invocation and hook setup.
- `/tmp/score-repository-source-proof.json`: all 34 tool source files match in
  both repository smoke images, whose configured development user is node.
- `/tmp/score-java-removal.log`: removal of OpenJDK selection and actual setup.
- `/tmp/score-no-host-python.log` and
  `/tmp/score-no-host-python-native.log`: Python/native Bazel delivery without
  system Python.
- `/tmp/score-no-python-all-bazel-sources.sha256`: 19 matching Bazel input files,
  including BUILD/module files, launcher/macros, Python data and native lockfiles.
- `/tmp/score-git-delivery-final.log`: Git package and console-boundary smoke.

These files are local run evidence. No log upload or other publication is part
of the goal. The [reference](tooling-reference-implementation.md) records the
architecture and reusable validation commands; the
[seven-PR sequence](tooling-pr-sequence.md) derives review boundaries from this
validated result. Full dependency locking, APT snapshots, an SBOM and reproducible
image rebuilds remain outside the agreed scope. No required verification remains
outstanding.
