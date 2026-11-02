<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Direct tool execution after provisioning

**M5 follow-up:** the [installer deletion milestone](tooling-retirement-milestone.md)
implements and exercises prepared strict host paths in all three candidates.
The traces and open-host-path findings below describe the earlier audit state.

Confirmed on 2026-11-01: the choice of tool manager must not impose a slow
wrapper on ordinary tool execution, inside or outside the DevContainer. uvx
was an example, not the scope of this requirement. This decision adds R7 to the
[decision record](tooling-decision-record.md).

## Required behavior

Provisioning may resolve dependencies, download artifacts, install runtimes and
validate pinned versions. An explicit update may repeat that work. After
provisioning, users must be able to execute the installed tool directly, using
its required runtime. Ordinary invocation must not require environment
synchronization, dependency resolution, build analysis or network checks.

A thin adapter may select a prepared path, set required environment variables
and forward arguments, working directory, exit status and signals. A wrapper
is not disqualified by its existence; its actual per-invocation work and
measured overhead matter. A required Python interpreter or other tool runtime
is part of the tool, not automatically an avoidable wrapper.

Existing Bazel labels remain compatibility/build entrypoints. They do not
replace the direct execution path. Optional commands such as uvx or a manager's
execution command can still be used; consumers must not have to use them to
start an already installed tool. First-use installation is provisioning, even
when one convenience command combines both phases.

Version selection must stay release-pinned on the strict path. Direct execution
does not authorize falling back to arbitrary host tools or a second maintained
version pin. In the selected container, installation and release checks already
establish the pin; per-call revalidation is unnecessary.

## Comparison criteria for all three candidates

The existing functional proofs do not measure startup overhead. Inspect the
actual generated launchers and invocation chain before rating a candidate.

The [2026-11-02 dynamic audit](../experiments/tool-manager-comparison/execution-evidence/README.md)
now checks starpls and codespell from each prepared M4 payload. These ratings are
bounded to those two commands in the prepared Linux runtime; they do not certify
all tools or a future strict host launcher.

| Concrete criterion | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| **E1: Actual native/Python process chain, without a manager/resolver/Bazel call** | 🟢 Native ELF; Python shebang | 🟢 Native ELF; Python shebang | 🟢 Native ELF; shell then Python in the same PID |
| **E2: Internet/socket behavior during version probe and real Python diagnostic** | 🟢 No socket operations in the samples | 🟢 No socket operations in the samples | 🟢 No Internet socket operations; Python wrapper attempts two local nscd socket connections |
| **E2: Required mutation of the installed payload** | 🟢 Runs with payload and root FS read-only; Python attempts optional bytecode-directory creation | 🟢 Same optional bytecode attempts; tools run successfully | 🟢 Runs with payload and root FS read-only; wrapper's `/dev/tty` open fails harmlessly |
| **E3: Repeated entrypoint cost against the underlying executable/interpreter** | 🟢 Measured; no extra native process or Python launcher | 🟢 Measured; no extra native process or Python launcher | 🟢 Measured; Python shell wrapper adds a paired median 1.836 ms in this run |
| **E4: SIGTERM/SIGINT reach the running tool, preserving its exit behavior** | 🟢 Four exposed/reference comparisons pass | 🟢 Four exposed/reference comparisons pass | 🟢 Four exposed/reference comparisons pass, including the Python wrapper |
| Native strict host launcher and other tools audited end to end | 🟡 Pending | 🟡 Pending | 🟡 Pending |
| Clean first-use and cached provisioning cost measured comparably | 🟡 Pending | 🟡 Pending | 🟡 Pending |

Green on E3 means the paired measurement and process audit exist, not that an
unagreed latency threshold has been met. A negative measured delta is ordinary
measurement variation, not a faster-than-direct architectural benefit.

The earlier [M4 checks](../experiments/tool-manager-comparison/maintenance-evidence/)
also run starpls's initialize/shutdown protocol. That tool attempts its own
background registry lookup; it is distinct from startup work imposed by a
launcher. The new starpls trace is a short version command, not project analysis.

For the still-open host routes and other tools, apply the same audit procedure:

1. Inspect one native CLI and one Python CLI on each supported execution route.
   Record command, symlinks, scripts, interpreter, environment setup and any
   manager/resolver processes. Include host and prepared-container routes;
   identify unavailable platform checks explicitly.
2. Provision the selected release explicitly. Run prepared commands with network
   disabled and identify launcher checks or mutation separately from the tool's
   own behavior. A successful offline command alone does not reveal its process
   chain.
3. Measure repeated short invocations and compare with the underlying executable
   or interpreter entrypoint from the same payload. Use the same machine,
   tool version, inputs and cache conditions for each pair. Report sample count
   and median/spread; do not rank different tools or versions against each other.
4. Report clean first provisioning, cached provisioning and prepared startup
   separately. Record which artifacts were already cached; do not infer clean
   installation cost from a warm run.

No numeric latency budget or performance winner has been established. Mandatory
resolution/synchronization/build analysis in the ordinary prepared path is an
architectural failure regardless of a favorable warm-cache timing. Thin adapter
overhead needs measurement before it can be judged material.

## Subsequent bounded inspection and timing

The [retirement investigation](tooling-installer-retirement.md) inspected the
actual prepared codespell entrypoints: mise/aqua use the installed Python
entrypoint directly; Nix sets runtime environment in a shell wrapper and execs
its Python entrypoint. No manager/resolver call appears in those sampled
scripts. Direct APM/OpenCode paths were also exercised in task-owned prefixes.
This narrows the open audit; it is not exhaustive tracing of all commands.

A common starpls 0.1.22 warm-start probe measured median direct execution at
1.013 ms, a thin shell forwarding to the same binary at 1.240 ms, and the warm
Bazel target at 91.806 ms (20 interleaved samples after two warmups per route).
[Conditions and raw samples](../experiments/tool-manager-comparison/retirement-evidence/baseline.warm-startup.json)
are retained. These are local measurements, not a manager ranking or cold-install
cost. They support separating fast prepared execution from provisioning and
retaining thin forwarding where useful. No numeric acceptance budget is adopted.

## Dynamic execution audit: what actually happens

The four criteria above address ordinary startup and process behavior rather
than adding more package-manager features to the requirements. All three M4
payloads run in the same instrumented Ubuntu runtime with `PATH=/usr/bin:/bin`,
UID 1000, networking disabled, a read-only root filesystem and read-only mounted
tool trees. Only scratch space and the report directory are writable. No manager
is installed in the common base. The Nix closure keeps its supported absolute
`/nix/store` paths; the other payloads keep their `/opt/score-tools` paths.

### E1: Process chain

`strace -f` follows process creation, executable replacement, filesystem and
socket calls. The record also retains script sources and resolved paths, because
a kernel-handled shebang does not produce a separate userspace `execve` event.

| Sampled path | mise | aqua + uv | Nix |
| --- | --- | --- | --- |
| starpls `version` | Direct upstream ELF | Direct upstream ELF | Direct Nixpkgs ELF with its runtime libraries |
| codespell `--version` and typo check | Entry script → system-Python-backed venv | Entry script → system-Python-backed venv | Bash wrapper → `.codespell-wrapped` → Nix Python |
| Explicit exec events for native/Python entrypoint | 1 / 1 | 1 / 1 | 1 / 2 |
| Additional non-thread child processes during these commands | 0 | 0 | 0 |
| Manager, package resolver or Bazel execution | None observed | None observed | None observed |

Nix's second exec replaces the shell in the same PID. It is a thin environment
adapter, not a resident supervisor, resolver or installation step. The Python
reference comparison preserves the wrapper's PATH and `PYTHONNOUSERSITE` settings
while starting its wrapped Python script directly. The mise/aqua references use
the same venv interpreter and entry script explicitly instead of its shebang.

### E2: Runtime dependencies and side effects

The exposed and reference Python paths both attempt five `mkdir` calls for
`codespell_lib/__pycache__` in the mise/aqua payloads. These fail with `EROFS`;
version checks and real typo diagnostics still return their expected results.
That is Python's optional import caching, not a manager synchronizing the
environment or a required writable installation. A bytecode-preparation choice
belongs to provisioning; no such optimization is applied by this audit.

Nix's shell wrapper attempts to open `/dev/tty` and makes two unsuccessful
`AF_UNIX` connections to `/var/run/nscd/socket`. The wrapped Python reference has
neither. These are local terminal/name-service probes by the wrapper/runtime,
not Internet access, package resolution or writes into the tool store. There
are no `AF_INET`/`AF_INET6` socket operations in any of the recorded samples.
No successful managed-payload mutation is required in these tests.

The conclusion is narrower than “tools never use the network”: user-requested
operations, language-server analysis and other commands can legitimately do so.
It also does not imply that every possible Python tool tolerates a read-only
installation merely because codespell does.

### E3: Paired startup measurements

There are **40 untraced samples per route after three warmups**, interleaved with
alternating order inside the same container. Each pair compares the exposed
entrypoint with the underlying executable/interpreter from its own payload.
The clock includes process creation and exit, not Docker startup or provisioning.
The following values are milliseconds; the full records include individual
samples, min/max, p10 and p90.

| Payload/tool | Exposed median | Underlying median | Median paired delta | Exposed p10–p90 |
| --- | ---: | ---: | ---: | ---: |
| mise / starpls | 0.636 | 0.642 | −0.005 | 0.599–0.721 |
| aqua / starpls | 0.664 | 0.672 | −0.000 | 0.619–0.715 |
| Nix / starpls | 0.723 | 0.720 | +0.004 | 0.664–0.858 |
| mise / codespell | 28.314 | 27.957 | +0.419 | 27.258–29.301 |
| aqua / codespell | 28.984 | 29.373 | −0.153 | 27.895–30.889 |
| Nix / codespell | 42.793 | 41.267 | +1.836 | 41.089–46.079 |

The paired delta is the median of pairwise differences, not the difference of
medians. Native invocation adds no manager layer. The Nix Python wrapper has a
small measured additional cost in this run. The larger Python startup time is
mostly present in its underlying interpreter/application path as well.

**Do not rank the managers by the Python totals.** mise/aqua use codespell 2.4.1
on Python 3.12; Nix uses codespell 2.4.3 on Python 3.14, with different packaging
and import paths. Only each within-payload pair isolates its entrypoint cost.
This run is neither a cold-start benchmark nor a measured first-install budget.
No numeric acceptance threshold has been adopted.

### E4: Aborting a running command

The native probe runs `starpls server`; the Python probe runs `codespell -` with
stdin held open. The harness waits until a tool thread is actually blocked
reading stdin before sending SIGTERM or SIGINT **to the original PID**. This
checks the running tool rather than merely interrupting its loader. A separate
session permits checking that no process remains in that test's process group.

| Tool / delivered signal | Exposed result, each candidate | Underlying reference, each candidate |
| --- | --- | --- |
| starpls / SIGTERM | Terminated by signal 15 | Same |
| starpls / SIGINT | Terminated by signal 2 | Same |
| codespell / SIGTERM | Terminated by signal 15 | Same |
| codespell / SIGINT | Exit 130 | Same |

All twelve exposed/reference comparisons pass, with no remaining process in the
created process groups. Nix's shell does not swallow the signal because it has
already exec'd Python. These stdin-blocked cases do not establish signal handling
for active project analysis, subprocess trees of arbitrary tools or a future
strict host adapter.

### Consequence for effort and architecture

This closes a concrete concern about the sampled prepared runtime: none of the
three needs a package manager, resolver or Bazel on ordinary invocation. It would
be wrong to reject a candidate merely because it has an optional manager `exec`
command or a thin shell entrypoint. Nix's additional Python exec and measured
cost are explicit; they do not establish a slow-wrapper failure.

The common work remains publishing prepared paths and implementing deliberate
release selection for strict host use. The process and signal checks belong in
acceptance for that future interface. These results do not supply a new reason
to pay a manager's migration cost; the
[maintenance/effort conclusion](tooling-installer-retirement.md) remains the
basis for that choice. Nix's separately demonstrated recovery/verification
capabilities remain a real additional benefit, not a runtime penalty inferred
from its name.

[Evidence and reproduction](../experiments/tool-manager-comparison/execution-evidence/README.md)
include complete compressed syscall traces, resolved paths and wrapper source,
paired raw timings, signal results, runtime identity and actual Docker commands.

## Existing runner modes and trust boundary

The selected S-CORE container is assumed to contain the correct pinned tool
versions. Both modes may execute its installed tools directly. The runner does
not need to revalidate each executable or route container invocations through
Bazel. Correct installation and release validation establish that trust.

| Environment | Convenience: `run-tool <tool> ...` | Strict: `run-tool --strict <tool> ...` |
| --- | --- | --- |
| Selected S-CORE container | Use the installed tool directly | Use the installed tool directly; trust the container's pins |
| Host outside the container | May use the available PATH executable; otherwise use the pinned delivery path | Bypass arbitrary host tools and use the selected release's pinned delivery path |

Keep the existing interface and argument/cwd/exit behavior. If the container
command is missing, the existing pinned fallback may still be used; this does
not require packaging every container-only tool for Bazel.

The current [`tools/run-tool`](../tools/run-tool) container PATH branch is
consistent with this trust assumption. Its container behavior is **not** a
strict-mode defect merely because it does not verify a version at every call.
This clarification revises #190's earlier demand to reject unverified PATH tools
inside containers. A future issue update should reflect the agreed boundary;
this local record does not change the published issue.
