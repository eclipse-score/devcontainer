<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Direct execution audit: E1–E4

The [comparison and interpretation](../../../docs/tooling-execution-paths.md)
cover process chains, socket/file side effects, paired startup costs and
SIGTERM/SIGINT behavior. These are prepared Linux runtime observations, not
completed host bootstrapping or an all-tool certification.

## Evidence

| Record | Contents |
| --- | --- |
| [Summary](summary.json) | Versions, trace counts, timing distributions and successful signal-case counts |
| [mise](mise.json), [aqua](aqua.json), [Nix](nix.json) | Resolved paths, wrapper source, significant syscall events, all timing samples and signal results |
| [mise run](mise.run.json), [aqua run](aqua.run.json), [Nix run](nix.run.json) | Actual Docker argv, exit status, stdout and stderr |
| [Provenance](provenance.json) | Instrumented image digest, host architecture, payload mounts, expected tool versions and UID |
| [Complete traces](traces.tar.gz) | All fifteen syscall traces, including successful and failed file reads; archive checksum in summary |

The trace archive contains only relative `mise/`, `aqua/` and `nix/` paths. Extract
it into a fresh scratch directory to inspect events omitted from the concise JSON
views. The JSON retains exec, socket, mutation-attempt and non-thread process
creation events; it is not a substitute for the full traces when auditing the
filter itself.

The runtime is the common Ubuntu comparison base plus strace 6.8. Instrumentation
is not part of any production candidate. Root and payload filesystems are
read-only; the report directory and `/tmp` are writable. Networking is disabled
at Docker level. The observed UID is 1000, `PATH=/usr/bin:/bin`, and HOME is a
scratch location. Package managers are absent from the common base and are not
called by the sampled commands. Payloads retain their absolute runtime paths.

The accepted M4 payloads are mounted read-only. No source pins, manager caches,
Python environments or Nix producer stores are modified by this audit.

## Reproduce

Prerequisites are complete M4 payloads at the recorded paths, Docker and Python
3. Run the host orchestrator as a normal user. The Nix input must be its complete
exported store tree, not a single copied executable. The probe reads entrypoint
paths and expected versions from the existing M4 runtime evidence.

Build the common instrumentation image from the repository root:

```bash
docker build -t score-execution-audit:20261102 \
  -f experiments/tool-manager-comparison/execution-evidence/Dockerfile .
```

The Dockerfile references the existing local comparison base. Its instrumentation
APT inputs are not a new locked production selection; the retained image digest
and strace version identify this recorded run. Rebuilding later may produce a
different instrumentation image, which the orchestrator records.

Choose a **new** workspace for each run:

```bash
python3 experiments/tool-manager-comparison/run-execution-probes.py \
  --workspace /tmp/score-execution-reproduction \
  --mise-payload /tmp/score-m4-mise/prepared-context-m4/opt/score-tools \
  --aqua-payload /tmp/score-m4-aqua/prepared-published-owner-final \
  --nix-store /tmp/score-m4-nix/production-context/experiments/tool-manager-nix/reference/out/m3-production/native/nix/store
```

The orchestrator invokes the same [runtime probe](../execution-probe.py) for all
three variants. It uses sequential containers with the same image, networking,
user, root-filesystem policy, PATH and test input. Each container is removed on
exit. The recorded full run completed with exit zero for every candidate.

Each payload produces five syscall traces: native version, exposed/reference
Python version, and exposed/reference Python typo diagnosis. The typo command
must report exit 65. The reference keeps the same interpreter/application; the
Nix reference also reproduces the shell wrapper's PATH and `PYTHONNOUSERSITE`.
There is no cross-version Python performance ranking.

Timing uses 40 samples per route after three warmups and alternating pair order.
`--samples` can change the sample count, but cannot turn this into a clean-install
benchmark. Timings are **not under strace**, and exclude Docker/container startup.
Both routes must return the expected version on every timed call. The record
retains samples and the median of paired differences, separately from the
exposed/underlying medians.

Signal checks start starpls in server mode or codespell on open stdin. They wait
for a thread blocked on a pipe read, then signal the original PID, compare the
exit status with the underlying reference and check the created process group.
Four exposed/reference cases per candidate pass. This does not exercise active
project analysis, terminal job control or arbitrary tools' subprocess trees.

The original recorded workspace is `/tmp/score-execution-20261102-confirmed`.
Only artifacts from that complete run are archived here. Scratch results of the
initial harness run remain outside the repository and are not additional samples
pooled into the timing tables.
