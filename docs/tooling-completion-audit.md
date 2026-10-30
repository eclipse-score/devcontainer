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

This audit preserves the [goal's full scope](tooling-refactor-goal.md). The goal
is not complete while any required item below remains outstanding. All changes
are local on `refactor/tool-management-reference`; no PR or publication exists
for this implementation.

## Requirements and current proof

| Goal requirement | Evidence | Status |
| --- | --- | --- |
| Every managed tool/helper has owned source, policy, selection and platform/update information | Validated/generated inventory contains 63 definitions across native, Python, APT, release/setup, feature, image, fixture, npm and optional helper providers; `sync_readme.py --check` passes. Baseline coverage and intentional boundaries are described below | Proven |
| One version authority; shared installation membership; unavoidable registrations checked | Literal Python owner, native lockfile owners, provider definitions and environment selections; generated sibling release versions and native hub/alias checks; selection/removal/registration checks in the shared reader | Proven |
| Published and repository environments retain capabilities, including non-root and platform behavior | Final-source amd64 image and full feature tests passed as vscode. Repository builds and derived installation/verification smoke images passed as node on amd64 and arm64. Earlier published arm64 image passed all feature tests with current checks. Final-source published arm64 build/tests remain pending | Outstanding |
| Native and Python Bazel delivery without host Python | Minimal Ubuntu image verifies neither python nor python3 is on PATH, runs real pre-commit 4.7.0 using uv-managed CPython, and separately runs native ShellCheck 0.10.0. Delivery-source hashes match the current launcher, Bazel macros, Python definitions and module configuration | Proven |
| Standalone uv from local Git, with packaged data and no Bazel/container installer dependency | `tools/tests/git_delivery_smoke.sh` passed at local code commit `e848cc4` outside the checkout; it checks the installed catalog and console script, real pre-commit, cwd, quoted/empty arguments and returned status. No source checkout or container installer is needed | Proven |
| Matching real Python package/version/entrypoint across three paths | Shared definition is pre-commit / 4.7.0 / pre-commit. Real Bazel, installed container and Git-selected uv executions report 4.7.0; launch/install argument contracts inspect the exact requirement and entrypoint | Proven |
| Generated docs, updates and meaningful drift checks use the final owners | README generation and check mode; Renovate derives native requests from lockfiles; digest refresh updates filenames/hashes and generated sibling versions or fails; tests reject selection, installed-version, package-state and process-boundary drift | Proven |
| Invocation/PATH/strict contract documented and tested; deliberate migration decision | `run_tool_test` verifies existing container/host/strict precedence and errors. `tools/README.md` and maintenance guide remove the PATH version-attestation claim and document explicit Bazel/uv choices; no downstream migration performed | Proven |
| Appropriate repository checks and affected image/delivery tests pass | 20 Python tests, both Bazel contract tests, repository hooks, final-source amd64 feature tests, Git smoke and both repository-platform smoke images passed. Final-source published arm64 verification remains required | Outstanding |
| Small PR breakdown with outcomes, dependencies, validation and working intermediate states | `tooling-pr-sequence.md` describes seven dependency-ordered PRs; keeps existing callers until replacements land together, identifies each usable intermediate state and its gate, and separates discovery commits from review boundaries | Specified; accept after final validation |

## Baseline coverage and version preservation

A read-only comparison against baseline commit
`0cc738794384cf32f08ba616c049bf8f3fb7124c` confirms:

- All 11 native command definitions, URLs, platform artifacts and checksums are
  byte-identical to the baseline native JSON files.
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

The preceding amd64 build is `score-tooling-reference:verified-amd64`. Before tests,
SHA256 comparisons proved that its embedded catalog reader, container installer,
provider definitions, environment selections, shell metadata bridge and both
feature installation scripts match the current sources. The full feature tests
then ran as vscode with only the test-project directory mounted read-only;
there was no tool or feature-test overlay.

The final builds `score-tooling-reference:final-amd64` and
`score-tooling-reference:final-arm64` include the Java selection guard from
`e848cc4`. They must pass the same source comparison and non-root feature tests. Linux arm64 CodeQL
omission is intentional and declared; the remaining selected tools must work.

The repository environment is built from its unchanged Dev Containers config on
both platforms. Derived smoke images copy the current tools, apply the repository
selection, switch to node, verify all selected commands/npm resolution, execute
Docker and Dev Containers CLI, and install a hook in a temporary Git repository.
The optional dive installer also passed artifact verification and execution in
disposable amd64 and arm64 development containers. Removing OpenJDK from a
disposable composition skips the actual Java setup block without querying javac
or changing the Java profile; the positive branch is covered by feature tests.

## Evidence locations for this local run

The reusable commands are in the maintenance guide, CI and
`tools/tests/git_delivery_smoke.sh`. Local execution evidence currently includes:

- `/tmp/score-baseline-policy-audit.json`: native, migrated policy and external
  configuration comparison against the baseline.
- `/tmp/score-precommit-final.log`: repository hook checks.
- `/tmp/score-tests-current-amd64.log`: all final-source amd64 feature tests.
- `/tmp/score-image-final-amd64.log` and `/tmp/score-image-final-arm64.log`:
  live final-source builds.
- `/tmp/score-tests-arm64-intermediate.log`: earlier arm64 installation's full
  functional checks; this does not substitute for the pending final image.
- `/tmp/score-repository-final-amd64.log` and
  `/tmp/score-repository-final-arm64.log`: repository environment installation,
  resolution, non-root invocation and hook setup.
- `/tmp/score-java-removal.log`: removal of OpenJDK selection and actual setup.
- `/tmp/score-no-host-python.log` and
  `/tmp/score-no-host-python-native.log`: Python/native Bazel delivery without
  system Python.
- `/tmp/score-git-delivery-final.log`: Git package and console-boundary smoke.

These files are local run evidence. No log upload or other publication is part
of the goal. Before closure, record the final image identifiers, fresh command
outcomes and remaining limits in the reference, then resolve every outstanding
row above against the actual sources/results.
