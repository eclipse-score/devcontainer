<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Common reference implementation milestone

**Direction:** continue mise, aqua and Nix equally. No candidate is selected.
All work stays local. This extends the earlier version probes into maintained
delivery code under each candidate's `reference/` directory.

This page records completed milestone 1. The subsequent
[repository integration](tooling-repository-milestone.md)
extends all three into real root consumers and built tooling images; its scope
is not an estimate of total migration percentage.

The [shared acceptance contract](../experiments/tool-manager-comparison/reference-milestone.md)
defines one checkpoint for all three. Each prepares Ruff, ShellCheck and
pre-commit; `published` selects all three and `repository` excludes ShellCheck.
The prepared release supplies runtime files and image provisioning, an ordinary
Python dependency package, and runnable simple Bazel targets.

## Common checkpoint result

All three completed the baseline and an isolated Ruff update through their same
maintained producer/check paths. 🟢 means demonstrated for this bounded reference;
it is not a production-readiness rating or a score to total.

| Observable criterion | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Prepared release with native inputs, runtime files and provisioning | 🟢 Complete selected install trees | 🟢 Native binaries and fixed Python environment | 🟢 Complete store closure and profile commands |
| Published Ubuntu runtime: all three tools, uid 12345, network denied | 🟢 Both releases | 🟢 Both releases | 🟢 Both releases |
| Repository runtime: Ruff/pre-commit work, ShellCheck absent from PATH | 🟢 Both releases | 🟢 Both releases | 🟢 Both releases |
| Real Bazel execution: Ruff, ShellCheck, pre-commit | 🟢 Versions and behavior fixtures | 🟢 Versions and behavior fixtures | 🟢 Versions and behavior fixtures |
| Normal uv project dependency and actual uvx execution | 🟢 Generated static package | 🟢 Generated static package | 🟢 Generated static package |
| Ruff update reaches runtime, Bazel metadata and resolved Python dependency | 🟢 0.11.13 → 0.11.12 | 🟢 0.11.13 → 0.11.12 | 🟢 0.17.2 → 0.14.6 |
| Other direct versions remain unchanged | 🟢 pre-commit 4.7.0; ShellCheck 0.10.0 | 🟢 pre-commit 4.7.0; ShellCheck 0.10.0 | 🟢 pre-commit 4.7.0; ShellCheck 0.11.0 |
| Bazel pre-commit can bootstrap Python with no host interpreter selection | 🟢 Fresh isolated managed Python | 🟢 Fresh isolated managed Python | 🟢 Fresh isolated managed Python |

The update versions are deliberate existing fixtures, not proposed downgrades.
Ruff/ShellCheck error fixtures and real local pre-commit hooks verify arguments,
caller working directory and exit behavior. Every prepared runtime uses the
unchanged shared external check. Its offline guarantee applies to the prepared
container; cold uv/Bazel dependency setup remains a separate online operation.

The extra Python-bootstrap check grew out of direct peer review and was applied
to all three with the same existing launcher. It downloaded managed CPython
3.15.2 in isolated directories. This does not establish a compiler-free bootstrap:
all three captures built PyYAML from source. Interpreter and initial dependency
resolution policy remain shared Bazel-adapter responsibilities, not a candidate
advantage or an adopted new Python pin.

## What is maintained

| Responsibility | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Authored tool versions | Native mise tool entries | aqua package entries; Python dependency groups | Package attributes selected from locked Nixpkgs inputs |
| Authored selection | Native mise configuration environments | aqua tags and native Python dependency groups | Native flake profile lists |
| Upstream preparation | mise backends install native tools and the Python environment | aqua copies native binaries; uv prepares the Python environment | Nix builds profiles and computes their runtime closure |
| Runtime handoff we maintain | Preserve complete selected install/venv trees at their required paths | Copy native binaries and preserve a Python environment at a fixed image prefix | Transfer the complete store closure and expose selected profile commands |
| Simple Bazel export we maintain | Translate resolved native artifact locks and archive layouts | Translate resolved aqua checksums and archive layouts | Export selected versions; resolve matching upstream portable archives and hashes |
| Python consumer export we maintain | Generate ordinary dependency extras from selected versions | Generate ordinary dependency extras from selected versions | Generate ordinary dependency extras from selected versions |
| Release binding we maintain | Prepare native selection, generated package and Bazel metadata together | Prepare native selection, generated package and Bazel metadata together | Prepare native selection, generated package and Bazel metadata together |

All three reuse the existing Bazel Python launcher and its baseline uv helper
definition. No candidate introduces a new consumer installer, universal tool
schema, complex-tool Bazel packaging or mandatory producer manager for uv users.
Generated dependency metadata contains the selected versions; consumers use
normal `uv` and `uvx` dependency resolution rather than querying a wrapper.

This table records integration responsibilities, not engineering hours. A native
manager's single interface does not eliminate our release/export code; conversely,
Nix's closure handling supplies runtime dependency ownership that the other
references do not claim. Judge whether those responsibilities are useful for
this repository before treating them as cost or benefit.

## Local implementations and evidence

The existing branches and worktrees remain separate; none is published:

| Candidate | Sibling worktree | Maintained implementation |
| --- | --- | --- |
| mise | `score_devcontainer-eval-mise` | `experiments/tool-manager-mise/reference/` |
| aqua + uv | `score_devcontainer-eval-aqua` | `experiments/tool-manager-aqua/reference/` |
| Nix | `score_devcontainer-eval-nix` | `experiments/tool-manager-nix/reference/` |

Each reference documents its producer prerequisites, prepare/check commands,
authoritative inputs, generated outputs and remaining responsibilities. Retained
evidence distinguishes authored Ruff changes from generated locks, Bazel
registrations and Python package metadata. Native profile semantics and runtime
paths may differ; the acceptance behavior is shared.

## Boundary of this checkpoint

This is a common delivery implementation for three real tools, not a completed
migration of the S-CORE image or entire catalog. Existing features, legacy OS
packages, complex tools, release hosting and long-term archival remain outside
this checkpoint. Actual macOS ARM execution remains unverified.

pre-commit exercises the Python delivery path relevant to #189. It does not
establish that every proposed Python tool or the full #189 change is migrated.
The container remains the default, uv/uvx a native consumer path, and Bazel a
limited CLI delivery path for suitable simple tools.

The earlier [qualitative complexity assessment](tooling-version-workflow-comparison.md)
remains a hypothesis to revise against this maintained code. It is not an
authorization to advance one candidate alone. Future common checkpoints should
name an unresolved architectural question and the same observable outcome for
all three, with fixes shared during implementation and reviewed across peers.
