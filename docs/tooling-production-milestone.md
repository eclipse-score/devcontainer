<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Full DevContainer integration: mise, aqua and Nix

Milestone 3 connects each candidate's prepared native/Python runtime to the
actual published DevContainer source and its existing local features. All three
remain local alternatives. The [shared contract](../experiments/tool-manager-comparison/production-milestone.md)
defines the acceptance boundary; the [previous milestone](tooling-repository-milestone.md)
records root Bazel/package consumption and the smaller tooling images.

## What changes in the architecture

The producer prepares the selected tools before the image build. A generated
handoff tells the existing feature installer which tools are already present.
The installer validates that handoff against current selections, then skips
their old native downloads and Python installations. Existing APT phases and
special setup still run.

This migrates tool delivery inside the full image. It does not replace Ubuntu,
common-utils, LLVM, CodeQL or Bazel's provider/cache/completion setup with a
tool manager. apm, opencode and starpls retain their existing delivery paths.
The installed commands remain available directly, including uv and uvx. Both
existing container run-tool modes continue to trust the installed tools.

For #189, pre-commit, pytest and basedpyright now use this same prepared handoff
inside the real image. The ordinary uv project/uvx dependency-consumption evidence
from milestone 2 remains applicable and is preserved; this checkpoint does not
claim to repeat those package-consumer probes.

## Integration responsibilities exposed by implementation

| Concrete responsibility | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Native and Python runtime being copied | Complete selected mise installation trees, including Python environments | Selected native executables plus prepared uv Python environments | Referenced Nix store paths and their closure |
| Python interpreter supplied by | Matching Ubuntu system Python in producer and target image | Matching Ubuntu system Python in producer and target image | Interpreter included in the copied store closure |
| Generated bridge to existing features | Current owner/selection metadata plus runtime handoff | Runtime handoff with feature selections, versions and executable hashes | Runtime handoff with command identity, versions and store paths |
| Expose commands to existing setup | Public executable links | Prepared bin directory on PATH | Public links to store executables |
| Connect preparation to the ordinary build | BuildKit named runtime context | Generated runtime directory in the normal build context | Temporary source/build context containing the prepared store closure |
| Keep old setup working with new paths | Preserve stable runtime prefixes and public commands | Resolve Bazelisk through PATH rather than assuming its old install directory | Activate commands after common-utils has supplied Python |
| Shared work independent of manager | Validate handoff; skip duplicate installs; retain APT and special providers | Validate handoff; skip duplicate installs; retain APT and special providers | Validate handoff; skip duplicate installs; retain APT and special providers |

These are observable implementation duties, not a score or an estimate of total
migration effort. All three need an adapter to the existing feature lifecycle.
The adapters differ in the runtime paths and dependency trees they preserve.
An integration defect that is fixed and shared is not evidence that the manager
cannot meet the requirement.

The independent mise producer check exposed a concrete dependency boundary:
preparing venvs in a generic Python image selected a managed interpreter under
disposable producer state. Its export looked complete but lacked that
interpreter. The corrected default producer uses Ubuntu 24.04, selects
`/usr/bin/python3` explicitly and disables managed-Python fallback. Fresh default
preparation verified all three Python environments use the target's interpreter.
This makes producer/target compatibility a maintenance responsibility for the
venv-based variants; Nix instead carries the interpreter in its store closure.
It does not remove Nix's need to integrate with the retained Ubuntu features.

Concurrent local builds and different candidate tool versions are not a build
speed or image-size benchmark. Existing system-package and feature work also
dominates much of these full builds. Those measurements do not establish an
integration-complexity ranking.

## Acceptance evidence

All three reached the same full-image checkpoint. 🟢 records an observed result
within this scope; cells are not scores.

| Observable criterion | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| Full Linux amd64 image with original pinned external/local feature chain | 🟢 | 🟢 | 🟢 |
| Original production suite as vscode, online as designed | 🟢 | 🟢 | 🟢 |
| Identical 44-command acceptance, uid1000 and network denied | 🟢 | 🟢 | 🟢 |
| Direct selected commands and both actual container run-tool modes | 🟢 | 🟢 | 🟢 |
| Real pre-commit hook, diagnostics/formatters, pytest and basedpyright | 🟢 | 🟢 | 🟢 |
| Provider-selected Bazel 8.6.0 available without network | 🟢 | 🟢 | 🟢 |
| Build logs show verified skips while APT and special setup continue | 🟢 | 🟢 | 🟢 |
| Focused missing/stale handoff and duplicate-install regression coverage | 🟢 | 🟢 | 🟢 |
| Missing preparation and unsupported platform rejected before Docker | 🟢 | 🟢 | 🟢 |
| Default/proxy Dockerfile handoff parity checked in source | 🟢 | 🟢 | 🟢 |

The [shared acceptance script](../experiments/tool-manager-comparison/repository-runtime-check.py)
is unchanged across candidates. Its [evidence directory](../experiments/tool-manager-comparison/production-evidence/)
preserves exact commands, expected selections, tested image identities and full
44-command transcripts. Only read-only check/expectation files are mounted;
runtime tools, Python environments and the warmed Bazel are inside the images.
The original production suite runs online for CA checks and the pycairo source
build; it is not described as offline.

mise and Nix also completed the full build through their adapted
`scripts/build.sh`. aqua completed its full production build through the
DevContainer CLI; its later standard-entrypoint guards were separately tested
without repeating that unchanged runtime build. The proxy-enabled path was
checked for matching source integration, not exercised behind a live proxy.
Current owner/root metadata, tool documentation and targeted source checks pass.

Source and complete candidate reports remain in the three sibling worktrees:
`score_devcontainer-eval-mise`, `score_devcontainer-eval-aqua` and
`score_devcontainer-eval-nix`, under `experiments/tool-manager-*/reference/`.
Their reports retain preparation commands and build/test evidence. No code,
image or report has been pushed or published.

## Scope that remains separate

The outer Node/Docker development container, remaining catalog tools, arm64 and
macOS execution, final source layout, release/update automation, hosting and
archival are outside this checkpoint. Proxy Dockerfile parity can be checked
without claiming a live corporate-proxy build. Supporting a prepared amd64
runtime must not silently put amd64 binaries into an arm64 image.

Nothing here establishes an overall migration percentage or selects a manager.

The subsequent [maintenance milestone](tooling-maintenance-milestone.md) changes
the native selections again. The image proofs above retain their M3 scope;
they do not validate full images assembled from those later selections.
