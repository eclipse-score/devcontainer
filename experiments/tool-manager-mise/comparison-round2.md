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

# mise: shared comparison, round 2

Date: 2026-10-31. Applies the parent's agreed C1/C2/C3 protocol after peer review.
**All three checks pass within the tested scope. No adoption ranking follows
from pass counts or from mise presenting one CLI.**

## Reproduce and inspect the evidence

From this worktree:

```sh
python3 experiments/tool-manager-mise/round2.py
experiments/tool-manager-mise/round2-runtime.sh
```

Preparation reuses the isolated mise 2026.10.24 binary and tool state described
in the first report, including the fresh version-only install under
`/tmp/score-mise-evaluation-fresh`. No global installation is performed.
Temporary release copies are created/deleted under the private evaluation root;
the maintained experiment pins remain Ruff 0.11.13 / pre-commit 4.7.0.

Evidence files:

- `round2-evidence.json`: exact argv/cwd/stdout/stderr/status for 10 real commands.
- `round2-maintenance.diff`: actual authoritative-config and generated-lock diff.
- `round2-runtime.log`: direct Ubuntu/non-root/network-disabled fixture output.
- `round2-updated-runtime.json`: exact Docker argv/result for the changed Ruff
  plus unchanged pre-commit in that same prepared runtime context.
- `release-run`: bounded selected-release/cwd-preservation adapter.
- `round2.py`, `direct-smoke.sh`, `round2-runtime.sh`: reproduction/verification,
  not production installer implementations.

## C1: independent maintenance and membership — tested pass

A temporary release copy changes Ruff from **0.11.13 to 0.11.12** through:

```sh
mise -E native,python -C RELEASE use --env native --pin aqua:astral-sh/ruff@0.11.12
```

The actual diff changes one maintained line in `mise.native.toml`; generated
`mise.native.lock` changes the Ruff version/specifier and three platform URLs,
asset IDs and hashes. `mise.python.toml` is byte-identical. Real selected-release
execution reports Ruff **0.11.12** and pre-commit **4.7.0**.

The published/native and repository-overlay selections reuse this authoritative
Ruff declaration. Round-one add/remove and ShellCheck-overlay execution remain
valid evidence; no extra arbitrary profile matrix was introduced.

The initial C3 fixture run used the baseline Ruff 0.11.13 and did not by itself
prove an update propagated into the runtime. A targeted final check closed that
specific gap: the already installed Ruff **0.11.12** produced by C1 and the
unchanged prepared pre-commit **4.7.0** were mounted into the same common Ubuntu
image, read-only, uid 12345, `--network=none`. Direct `--version` calls reported
exactly those versions. Exact argv/output are in `round2-updated-runtime.json`.
Thus the changed selected native version was observed on the host and in the
prepared runtime; no second version pin or re-packaging was needed. The full
fixture checks remain at the baseline, and no production image build is claimed.

Ordinary maintenance:

1. Edit a native pin, or use `mise use --env native --pin ...`; install refreshes
   its existing generated native lock.
2. Edit a Python tool pin, or use the equivalent command for the Python config.
   Its unlocked direct selection does not require a Python graph or runtime pin.
3. Choose the intended native/Python/repository environments, prepare them at
   image build time, and regenerate the bounded Bazel metadata if that consumer
   remains supported.

The split native/Python lock policy is a real convention to maintain. It avoids
requiring full Python locks but must be understood in profile/automation changes.

## C2: pinned host invocation from a hostile consumer — tested pass

`release-run RELEASE TOOL ARGS...` explicitly selects a prepared release config
through mise's `-C`, runs `mise exec`, then restores the caller's directory before
executing the real tool. It is a small experimental adapter, not a complete
public `run-tool` implementation or Git-release package.

The new optional `SCORE_MISE_PROBE_HOST_PATH` setting lets the existing isolated
harness pass the hostile host PATH into mise. The test therefore does not merely
hide the fake commands before the manager sees them. Managed tool paths must win.

Executed from a temporary consumer Git root with spaces in its nested path:

| Input / check | Actual observation |
| --- | --- |
| Consumer `mise.toml` pins both tools to nonexistent 0.0.0 | Explicit release still selects Ruff 0.11.12 / pre-commit 4.7.0 |
| Fake `ruff` and `pre-commit` precede the normal host PATH; they mark invocation and exit 97 | Neither fake runs; marker is absent |
| Relative `fixture with space.py`, containing `import os` | Real Ruff reports F401 and returns 1; demonstrates argument/cwd forwarding |
| `pre-commit run observe-cwd --all-files --verbose` | Real local system hook runs in consumer root, prints that path and validates argument `marker value`; tool returns 0 |
| Same hook with deliberately wrong argument | Real hook fails; pre-commit returns 1 through the adapter |

Mise manager and selected tool preparation are prerequisites for this tested
native route. No Container or Bazel is involved in C2. The adapter preserves
selected configuration and tool semantics; it does not implement a generic
command allowlist or forbid every possible consumer override. A production
strict runner must deliberately bound its registered commands/config sources.

The tested `-C` selection changes process cwd, so the probe needs its explicit
restore step. Aqua's peer reports that `aqua -c ABS_CONFIG exec` and uv's
`--no-project --no-config --with-requirements ABS_FILE` already preserve cwd.
This is a concrete difference between the tested calls, not proof that no other
mise-native configuration-selection pattern could avoid the restore.

A uv-only route would use release-derived Python metadata and standard uv
execution, as the other peers demonstrated. That can avoid installing mise on
Python-only consumers but retains an export/package/selection responsibility.
This round did not build a second full public launcher merely to duplicate that
route. The exact Git-package interface remains unimplemented for all candidates.

## C3: direct prepared Ubuntu runtime — tested pass

The script verifies and uses the common image:

```text
score-tool-manager-comparison-base:20261031
sha256:1b1ebf493ffb1a5a3a4d3c4c2a822cfe0da563d7028159078b0a02a12122a28d
```

`docker run --network=none --user=12345:12345` receives read-only mounts of only:

```text
/tmp/score-mise-evaluation-fresh/data/installs/aqua-astral-sh-ruff/0.11.13
/tmp/score-mise-evaluation-fresh/data/installs/pypi-pre-commit/4.7.0
```

These same absolute paths are retained inside the runtime. PATH contains Ruff's
`.mise-bins` symlink directory, pre-commit's `bin`, `/usr/bin` and `/bin`. The
pre-commit script's absolute venv shebang resolves inside its retained directory;
that venv's Python symlink points to **`/usr/bin/python3`**, supplied by the
common Ubuntu base (**3.12.3**). No private Python runtime/store is required for
this prepared version-only environment. Different environments could have other
runtime requirements; this is not a general portability claim.

Only a writable tmpfs `/work` supplies consumer files/home. No changes were
needed to the task-created install permissions: uid 12345 can traverse/read them.
The script checks that mise/aqua/Nix/uv are absent from runtime command lookup.
The manager, uv binaries, manager cache and installation helpers are not mounted.

Actual output: Ruff **0.11.13**, pre-commit **4.7.0**, Ruff F401/exit **1**, and the
local hook **Passed** while printing `/work/consumer` and validating its argument.
Neither tool installation nor a runtime manager executes. The network namespace
has no network. This closes the previous direct-execution/non-root gap for this
small selection; it is not a complete S-CORE image or archival test.

For a production prefix, perform installation at build time at that final path
and expose corresponding direct bin paths or stable symlinks. Moving this venv
arbitrarily after creation would break absolute references; the fixed-prefix
constraint applies just as it does to a directly uv-created venv.

## What remains maintained: compare responsibilities, not branding

| Responsibility | Tested mise approach | aqua plus uv approach from peer evidence |
| --- | --- | --- |
| Native version and artifact integrity | Native TOML pin + generated native URL/hash lock; document registry/provenance policy | Pinned registry/native YAML + generated checksum list with enforcement explicitly enabled |
| Python direct tool version | Python TOML entry; mise calls configured uv | Standard requirements pin; explicit uv command/venv |
| Python runtime/image preparation | Keep venv/interpreter paths valid and readable; tested system Python suffices | Same fixed-venv/runtime requirement; peer also uses the common system Python |
| Environment membership | Maintain config-environment selection and native/Python lock split | Maintain native tags and requirements selections; use `cp` for fixed native output |
| Lightweight host release | Tested manager bootstrap plus explicit config/cwd adapter; uv-only export remains possible | Two explicit native/backend invocations; existing cwd behavior needs no restore in the peer's probe |
| Existing simple Bazel interfaces | Own export/registration integration; Ruff example contains layout mapping | Own equivalent export/registration integration; Ruff bridge was actually executed in round one |
| Public Git-release uv package, if selected | Package/export Python definitions and keep a thin runner | Package/read requirements and keep a thin runner |

Observed mise benefit: dependency ordering and tool/bin discovery are upstream
features, not separate generic code in this repo. Observed counterweight:
profile/lock-policy conventions and the tested cwd/config adapter remain ours.
The probes do not quantify long-term maintenance or demonstrate that either
candidate's total remaining integration is smaller. Nix's native closure and
multiple locked package-set inputs are another valid ownership model; evaluate
their demonstrated steps rather than assuming a custom recipe is necessary.

## Remaining gaps and cross-review

Actual macOS ARM execution remains unavailable. Existing platform metadata is
not re-counted as execution. A production image, full tool inventory, complete
archive/prefetch policy and the final public release/bootstrap interface remain
open. No new general Bazel exporter was built: metadata matching, aqua's existing
Bazel run and Nix's version export remain differently scoped evidence.

Both peers received this report for challenge. I read their completed round-two
reports; the Nix C1 authored diff, C2 consumer probe and C3 runtime probe were
also inspected. Review observations:

- **Nix:** C1 actually builds the changed pre-commit package from a second locked
  input; C2 honestly uses exported uv requirements instead of claiming a native
  Nix host test; C3 carries the complete prepared closure. No custom recipe or
  universal portability claim is hidden by the pass result. Nix's reviewer found
  this mise report's update/baseline distinction and ownership accounting sound.
- **aqua:** Fresh `cp` tag outputs establish actual membership; the targeted C1
  runtime version check is separate from baseline behavioral fixtures. Its
  explicit aqua/uv calls preserve cwd without the tested mise restore step, but
  the report does not turn that into a total maintenance ranking. Its fixed venv
  and system-Python conditions are equivalent to this runtime probe.
- Both alternatives still need selected-release retrieval/public dispatch and
  bounded Bazel integration. Those unfinished responsibilities are not unique
  mise disadvantages or advantages. No extra tests are warranted merely to
  increase evidence counts.

Aqua's reviewer also inspected this report, `release-run`, the runtime shell and
targeted update evidence: no factual objection; fixed-path/Python handoff and
ownership accounting agree with its own result. The smaller aqua cwd adapter is
a local interface difference, not an overall winner. Both peers consider the
bounded checks complete; no further test expansion is proposed.

The parent retains the architecture decision; this report makes no new ranking.
