<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Aqua M7 final handoff

**Result: ARM64 published profile prepared and executed with one explicitly
documented exception.** The shared M7 contract forbids nested agents/CLIs, so I
completed this candidate directly rather than invoking the generic local
`codex` CLI.

## What ran

- Used cached `score-tooling-reference:final-arm64`
  (`sha256:b36448960057f54745f841561338487c5e9e2128526113c24b4861a7cf0f065a`)
  as Ubuntu 24.04/Python 3.12.3 substrate. The host is x86_64; Docker ran
  `linux/arm64` under QEMU and the container reported `aarch64`.
- Staged only 41 KiB of maintained Aqua owner, bootstrap, provisioner, Python
  command-catalog, and runner source under `/tmp/score-m7-aqua/source`.
- Ran the maintained bootstrap and published provisioner as UID/GID 1000 with
  network for Aqua/PyPI. Aqua 2.65.2 installed the current Linux ARM64
  published native and Python selection into fresh
  `/tmp/score-m7-aqua/prefix-arm64-published`.
- The real Aqua `cp` log again shows transitive `cli/cli` v2.102.0 `gh` output
  for `uv`. M6's private staging/promotion kept it out: the fresh `bin`
  inventory exactly matched all 17 selected command identities, with no `gh`.
- Ran with UID/GID 1000, network disabled, `UV_OFFLINE=1`, Python downloads
  disabled, and the prefix mounted read-only. Fifteen selected command version
  checks and the BasedPyright language-server initialize/shutdown check
  succeeded. Pytest and py.test passed a real test; uvx ran pytest offline;
  basedpyright typechecked; codespell passed; Ruff emitted the expected F401
  diagnostic and exit 1. Direct and strict `run-tool` resolved to the prefix;
  Aqua/Bazel interception markers stayed false.

## Remaining limit

Bazelisk 1.27.0 is present at the selected path but was not executed. Its
`--version` and `--help` dispatch to a Bazel engine, contrary to M7's no-Bazel
runtime constraint. Two attempts were stopped before an engine ran and are
retained in the raw log directory. No Bazelisk execution result is claimed.
All other selected commands were executed. macOS ARM and native ARM hardware
were not tested; no full image was built.

The macOS ARM configuration review found checksummed Darwin/arm64 assets for
all ten native published packages and the bootstrap. Starpls and APM local
registries also declare ARM-Mac support. Python requirements have no explicit
per-OS allowlist and remain unverified on macOS.

## Checks and artifacts

- `python3 -m unittest tools.tests.test_provision_host_tools tools.tests.test_aqua_python_package` — 13 passed.
- Targeted Ruff check/format, Python compilation, `bash -n` on the replay script,
  JSON acceptance, report whitespace checks, and `git diff --check` passed.
- Candidate output is 1.4 GiB total: 676 MiB prefix plus 750 MiB Aqua/uv
  caches. Free disk remained 7.1 GiB, above the required 4 GiB floor.
- Exact container commands: `/tmp/score-m7-aqua/commands.sh`.
- Compact result with owner digest, 11 source hashes, exact command paths,
  versions, runtime conditions, failures, and macOS metadata:
  `/tmp/score-m7-aqua/result.json`.
- Raw logs and runtime JSON: `/tmp/score-m7-aqua/logs/` and
  `/tmp/score-m7-aqua/results/runtime-smoke.json`.
- Candidate evidence: `/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/experiments/tool-manager-aqua/reference/README-m7.md`
  and `/tmp/score-m7-aqua/progress.md`.

No candidate production source needed repair in M7. The existing M6 selected
output fix was exercised against Aqua's real transitive `gh` copy. No commits,
pushes, publications, or shared comparison-document edits were made.
