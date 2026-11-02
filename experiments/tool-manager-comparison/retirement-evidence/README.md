<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Installer-retirement investigation evidence

The [conclusion](../../../docs/tooling-installer-retirement.md) separates actual
probes, source audits and proposed migration work. All artifacts are local
checkpoint evidence from 2026-11-01; none is a published installation API.

| Record | What it establishes |
| --- | --- |
| [Tracked callers](baseline.callers.json) | Actual feature, repository, update and metadata callers, including hidden directories |
| [Baseline host commands](baseline.host.json) | Native/Python task-local provisioning and direct functional execution |
| [Real baseline update](baseline.update.json) and [lock](baseline.shellcheck.lock.json) | Actual ShellCheck 0.11.0 refresh and execution after the archive-path repair |
| [Warm startup samples](baseline.warm-startup.json) | Direct/forwarded/warm-Bazel invocations with recorded conditions; not a manager ranking |
| [Prepared entrypoint sources](prepared.launchers.json) | Representative generated codespell launchers, not exhaustive process tracing |
| [mise](mise.retirement.json) | Exact APM/OpenCode preparation, runtime-tree observations and platform artifact comparison |
| [aqua](aqua.retirement.json) | Standard/local recipes, executable-only copy failure, direct complete-tree success and retirement boundaries |
| [Nix final record](nix.retirement.json) | Candidate investigation finalized with parent APM and source-build CLI checks; binary route remains sufficient |
| [Nix exact binary package](nix.exact-opencode.json) | Parent's working exact-version binary derivation, preserving the embedded application |
| [Nix task flake](nix.exact-opencode.flake.nix) and [lock](nix.exact-opencode.flake.lock) | Reproduction inputs for that bounded Linux binary derivation, not production package owners |
| [Registry lookup](aqua-latest-registry.json) | Default-branch file lookup for the two missing pinned-registry identities |
| [Package lookup](nix-latest-opencode.json) | Default-branch OpenCode version at lookup time; no newly locked input/build implied |

Baseline native control commands, from the main checkout with ordinary Python
and uv available:

```sh
python3 tools/internal/devcontainer/install.py install ruff shellcheck starpls \
  --destination /tmp/score-retirement-baseline/bin
python3 tools/internal/devcontainer/install.py install-python pre-commit \
  --uv uv --bin-dir /tmp/score-retirement-baseline/bin \
  --tool-dir /tmp/score-retirement-baseline/python-tools
```

The shared Python metadata control is separately reproducible with
`../managerless-probe.py --output /tmp/score-effort-control`. The root update
regressions run with
`python3 -m unittest discover -s tools/tests -p test_refresh.py`.

Candidate ledgers contain original task paths and command observations. The
mise source report lives in the sibling evaluation worktree under
`experiments/tool-manager-mise/reference/README-retirement.md`; aqua's report
is `/tmp/score-retirement-aqua/reference/README-retirement.md`; Nix's source report
is `/tmp/score-retirement-nix/reference/README-retirement.md`. The primary Nix
ledger was finalized by the parent using direct reproductions after the candidate
package probes and source audit. Relative references
inside those original reports are not a promise that all their temporary inputs
are copied here. Provenance is recorded without copying caches, tool payloads
or full image artifacts into the repository.

The early synthetic archive-update fixture remains in `../effort-evidence/`;
it is evidence of the bug before the repair and contains intentionally mocked
hashes. It must not be confused with the real update lock in this directory.
