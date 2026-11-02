<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Aqua M7 — Linux ARM64 execution

## Result

The maintained Aqua published profile was provisioned for Linux ARM64 and
executed from a fresh prefix under QEMU. The existing
`score-tooling-reference:final-arm64` image was used only as Ubuntu 24.04 and
Python 3.12.3 substrate. Its old tools were not counted: the runtime required
all 17 names in the fresh `/opt/score-tools/bin` to match the current published
owner selection and resolved each executed tool to that prefix.

Provisioning used the maintained `bootstrap_aqua.py` and
`provision_host_tools.py` as UID 1000 with network access for Aqua and PyPI.
Runtime checks used UID 1000, `--network none`, `UV_OFFLINE=1`, disabled Python
downloads, a read-only prepared prefix, and the cached runtime uv wheel
directory. The Docker engine ran the ARM64 image on the x86_64 host through
QEMU; this is not a native ARM hardware result or a full Dev Container image
build.

The real Aqua log shows why M6's selected-output promotion matters: even with
explicit selected command names, Aqua resolves `cli/cli` v2.102.0 as part of
`uv` and places its `gh` file in the private `cp` output. The provisioner
promoted only owner-selected names, so the fresh prefix contained no `gh` and
matched the 17-command selection exactly.

Sixteen selected commands were executed: 15 version checks plus a successful
BasedPyright language-server initialize/shutdown exchange. The only
non-executed selected binary is Bazelisk 1.27.0. Its `--version` and `--help`
arguments dispatch to a Bazel engine; M7 forbids a Bazel invocation. Both
attempts were stopped before an engine ran and are retained as failed attempts.
No result is claimed for Bazelisk execution.

| Selected command | Owner version | ARM64 result |
| --- | --- | --- |
| actionlint | 1.7.7 | Executed; reported Linux/arm64 build. |
| apm | 0.35.0 | Executed from the retained `lib/apm` runtime tree. |
| basedpyright | 1.35.0 | Executed; checked a typed Python file with zero diagnostics. |
| basedpyright-langserver | 1.35.0 | Executed; LSP initialize returned capabilities and clean shutdown. |
| bazelisk | 1.27.0 | Present at the selected prefix path; not executed because its CLI dispatches to Bazel. |
| buildifier | 8.2.1 | Executed version check. |
| codespell | 2.4.1 | Executed a clean-file check. |
| opencode | 2.2.3 | Executed version check offline. |
| pre-commit | 4.7.0 | Executed version check. |
| py.test | 9.0.2 | Executed a Python test; 1 passed. |
| pytest | 9.0.2 | Executed the same Python test; 1 passed. |
| ruff | 0.11.12 | Executed version check and a real F401 failing diagnostic (exit 1). |
| shellcheck | 0.10.0 | Executed version check. |
| starpls | 0.1.22 | Executed version check. |
| uv | 0.13.6 | Executed; reported `aarch64-unknown-linux-musl`. |
| uvx | 0.13.6 | Executed version check and ran cached pytest offline; 1 passed. |
| yamlfmt | 0.17.0 | Executed version check. |

Direct `tools/run-tool ruff --version` and strict
`tools/run-tool --strict actionlint -version` both resolved to the fresh prefix.
Runtime manager/Bazel interception markers remained false. The negative Ruff
fixture produced `F401 [*] \`os\` imported but unused` and exit code 1, as
expected.

## Reproduction commands and artifacts

The exact named, labeled Docker invocations are preserved in
`/tmp/score-m7-aqua/commands.sh`. Run `bash /tmp/score-m7-aqua/commands.sh` to
repeat the ARM provisioning and offline runtime checks. The script stages no
repository-wide source tree: its inputs are the 41 KiB allowlist under
`/tmp/score-m7-aqua/source` plus the small `run-tool` and runtime smoke files.
It labels both containers `score-m7-platform.candidate=aqua`.

The two commands use the cached base image and these essential controls:

```text
Provision: --platform linux/arm64 --network bridge --user 1000:1000
Runtime:   --platform linux/arm64 --network none --user 1000:1000
Runtime:   prefix mounted read-only at /opt/score-tools
Runtime:   UV_OFFLINE=1 UV_PYTHON_DOWNLOADS=never PIP_NO_INDEX=1
```

| Evidence | Path |
| --- | --- |
| Compact result, exact paths, commands, source hashes, and platform context | `/tmp/score-m7-aqua/result.json` |
| Successful provisioner log, including Aqua's staged extra `gh` | `/tmp/score-m7-aqua/logs/arm64-provision-retry.log` |
| Successful non-root offline runtime log | `/tmp/score-m7-aqua/logs/arm64-runtime-final2.log` |
| Executed command/version and functional results | `/tmp/score-m7-aqua/results/runtime-smoke.json` |
| Candidate progress and failed attempts | `/tmp/score-m7-aqua/progress.md` and `/tmp/score-m7-aqua/logs/` |
| Fresh published prefix | `/tmp/score-m7-aqua/prefix-arm64-published` |

The maintained Aqua owner digest was
`bbb68b4da49c1efa3498faca5272412bb90a0b557636e2c6fa48972e726fa38c`. The
result JSON records SHA-256 for all 11 staged maintained source/owner files.
The Linux ARM64 Aqua bootstrap was 2.65.2, verified against the existing
`linux/arm64` owner checksum. Selected native versions and Python requirements
are read from `tools/owners/aqua/aqua.yaml` and `pyproject.toml`; no pins
changed. `basedpyright==1.35.0` resolved its ARM Python dependency
`nodejs-wheel-binaries==24.19.0` through uv.

The prefix used 676 MiB and its fresh Aqua/uv caches used 750 MiB. Total M7
candidate output stayed near 1.4 GiB; free disk was 7.1 GiB after the checks,
above the 4 GiB stop floor. No full feature image, new base-image pull, global
prune, or large source-context copy was performed.

## macOS ARM configuration review

No macOS command was executed. The existing Aqua checksum environment list
includes `darwin/arm64`, and the checksum file contains Darwin ARM assets for
all ten published native packages. The Aqua 2.65.2 bootstrap also has a
Darwin/arm64 archive and checksum. The local starpls recipe declares
`darwin/arm64`; the APM recipe declares both Darwin architectures. Python
published pins have no explicit per-OS allowlist in `pyproject.toml`; uv would
resolve compatible artifacts, but macOS ARM resolution and execution remain
unverified. This is configuration evidence only.

## Responsibility ledger

| Responsibility | One-time M6/M7 integration | Recurring owner or mechanism |
| --- | --- | --- |
| Native version and platform selection | M6 added explicit staging/promotion of only selected Aqua command names; M7 found no source repair was needed. | `tools/owners/aqua/aqua.yaml` owns selected versions/tags; `aqua-checksums.json` and local registries own download identities and platform assets. |
| Aqua bootstrap | No M7 change. | `aqua-bootstrap.toml` owns the build-time manager version and checksums for declared platforms. |
| Python tools and entrypoint aliases | No M7 change. | `pyproject.toml` owns Python package versions/groups; `python_tools.bzl` owns existing console-script identities such as `py.test` and `basedpyright-langserver`; uv installs them. |
| Runtime command surface and safety | M6 owns prefix/profile signatures, foreign/user guards, selected-output promotion, and safe deselection. M7 exercised that surface on ARM64. | SCORE maps selected owner commands into the public direct bin, keeps APM's adjacent runtime tree, and preserves direct/strict runner behavior with Bazel fallback for ordinary missing-command compatibility. |
| Package resolution | No separate Aqua ARM installer was added. | Aqua resolves and downloads architecture-specific native assets; uv resolves Python packages and their platform dependencies. |
| Local package release | No M7 change. | Maintained `tools/internal/aqua/` generation/check commands consume the existing owners; release hosting and public identity remain undecided. |

## Limitations and failed attempts

- Bazelisk execution remains unverified because its selected CLI arguments
  dispatch to Bazel, which M7 prohibited. The binary is present at the selected
  version/path; no Bazel runtime result is inferred from that.
- Linux ARM64 execution used QEMU on x86_64. Native ARM hardware and macOS ARM
  execution were not tested.
- A first provision attempt lacked a writable bootstrap mount. The corrected
  run mounted one and succeeded; see `arm64-provision.log` for the failed
  attempt.
- Two runtime attempts were stopped at Bazelisk dispatch, and one harness-only
  attempt used an unsupported pytest cache flag and omitted the language
  server's `--stdio` option. Those attempts are retained but are not counted as
  passes; the final corrected runtime log passes all remaining checks.
- No full Dev Container image was built. M7 validates the maintained prepared
  published selection on the ARM64 OS substrate, not the complete feature
  image or a hosted release flow.
