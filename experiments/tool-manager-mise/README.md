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

# mise: bounded tool-management experiment

Evaluated locally on 2026-10-30 with mise **2026.10.24**, Linux x86_64.
Worktree: `score_devcontainer-eval-mise`, branch `eval/tool-manager-mise`.
No production changes, image builds, pushes or publication.

## Verdict

**mise fits the tested direct-tool/version workflow with little custom code.**
Ruff 0.11.13 and pre-commit 4.7.0 install and run from native mise configuration;
ShellCheck can extend the repository environment without repeating shared pins.
The simple Python path needs uv, which mise can bootstrap from configuration;
it does not require us to maintain a Python runtime pin or dependency graph.

The remaining custom integration is bounded Bazel metadata export and existing
consumer compatibility. This experiment does not show universal tool coverage,
full image provisioning, offline archival compliance or actual macOS execution.

## Maintained inputs and generated outputs

| File | Role |
| --- | --- |
| `mise.native.toml` | Authoritative Ruff version, native aqua backend |
| `mise.python.toml` | Authoritative pre-commit and uv versions; no Python dependency lock |
| `mise.repository.toml` | Additional repository tool: ShellCheck |
| `mise.toml` | Empty common root; no repeated tool selections |
| `mise.native.lock` | Generated Ruff URLs/hashes for Linux x64/ARM64 and macOS ARM64 |
| `generated/ruff.lock.json` | Generated existing-multitool-compatible artifact metadata |
| `generated/python_tools.bzl` | Generated pre-commit metadata usable by the existing Python Bazel macro |
| `export-bazel.py` | 54-line bounded export example; includes Ruff-specific archive layout knowledge |
| `mise-probe` | 18-line experimental harness isolating state and selecting native/Python environments |
| `evidence.json` | Captured outputs/exit statuses from eight smoke and maintenance commands |

Multiple configuration files are intentional: the requirements allow different
configs in one folder. All tool versions have one hand-maintained owner. Lock
and exported versions are derived, not independently maintained decisions.

## Commands and observed results

Run these from this worktree:

```sh
experiments/tool-manager-mise/mise-probe install
experiments/tool-manager-mise/mise-probe exec -- ruff --version
experiments/tool-manager-mise/mise-probe exec -- pre-commit --version
experiments/tool-manager-mise/mise-probe -E native,python,repository exec -- shellcheck --version
python3 experiments/tool-manager-mise/export-bazel.py
```

The harness defaults to `-E native,python`; the expanded selection adds the
repository overlay. Output was Ruff **0.11.13**, pre-commit **4.7.0**, ShellCheck
**0.10.0**. A second empty mise state installed all three common tools in about
four seconds on this host/network and ran pre-commit. This is an observation,
not a performance benchmark or a guarantee for other networks.

Additional executed checks:

- Ruff on `import os` with `--isolated`: F401 diagnostic and exit **1**.
- pre-commit in a temporary Git repository, using a local `language: system`
  hook calling the host's `python3`: **Passed**, exit **0**. No remote hook
  environments were involved. Providing arbitrary hook dependencies remains the
  consumer's responsibility.
- `mise use --env native --pin aqua:astral-sh/ruff@0.11.12`, then execution:
  **0.11.12**. The same command restored **0.11.13** and refreshed the lock.
- `mise use --env repository --pin aqua:astral-sh/ruff@0.11.13` followed by
  `mise unuse --env repository --no-prune aqua:astral-sh/ruff`: native config
  editing adds/removes a request. The temporary overlay override was removed;
  the final shared Ruff pin remains solely in the native config.
- Ruff's generated Bazel artifact records matched the existing repository
  lockfile exactly for version, URL, SHA256, extraction path and platform.
- Installed Ruff/pre-commit also ran directly using the paths returned by
  `mise bin-paths`, with `UV_OFFLINE=1`, without invoking mise or an installer.
  This demonstrates direct execution, not a network-denied offline test.

To add a different repository-only tool, maintain a single native entry in
`mise.repository.toml` (ShellCheck demonstrates the final result). Removing a
request removes it from the intended environment; uninstalling old cached
versions is a separate lifecycle choice.

## Locking: optional behavior, not an inflated requirement

The initial single-file configuration containing Ruff, uv and pre-commit worked
with plain `mise install` before any lock existed. That is sufficient for the
confirmed same-tool-version requirement. No manually described transitive
packages and no interpreter pin were necessary.

Current mise adds stronger behavior when a common `mise.lock` exists:
`mise lock` can generate a PyPI dependency-graph sidecar; subsequent ordinary
installs can populate that graph even after a targeted native-only lock command.
The initial graph install required an explicitly discoverable Python interpreter.
A managed Python declaration worked, but adds a runtime decision not required by
our scope. An old Python 3.12.3 artifact also lacked the attestations required by
mise's current defaults; Python 3.12.16 installed with verification enabled.
Neither issue is a blocker for plain version-only Python delivery.

The final small experiment uses mise's native config environments to separate
these policies: `mise.native.lock` belongs to `mise.native.toml`; the Python
config has no lock. Executed `mise -E native,python install` kept this separation,
including in a fresh isolated mise state. No Python sidecar or managed Python
pin is present in the final experiment. This uses documented per-environment
lock ownership; it is not a custom resolver.

See [lock ownership and behavior](https://mise.jdx.dev/dev-tools/mise-lock.html),
[settings](https://mise.jdx.dev/configuration/settings.html#lockfile), and
[PyPI installs](https://mise.jdx.dev/dev-tools/backends/pypi.html).

## Container, host and platforms

Proposed container integration: install selected environments at build time into
a stable system-owned mise data directory, retaining Python venv/runtime paths;
expose installed tool bin paths or stable symlinks on image PATH. Run the tools
directly as the development user. Container strict mode trusts this prepared
image exactly as agreed. No per-call version check or Bazel rerouting is needed.
The direct-installed execution above is evidence for the execution approach;
non-root image permissions and IDE setup still require an actual image check.

Outside the container, a release-selected checkout/config plus `mise exec`
provides the selected environment. The final production runner must retain the
caller's cwd and control config selection rather than trust arbitrary consumer
config overrides. This experimental harness deliberately changes into its own
config directory; it is not a production `run-tool` implementation.

Linux x86_64 was executed. Generated Ruff artifact metadata includes Linux ARM64
and macOS ARM64 with the same baseline URLs/hashes already used by the repo.
Mise itself publishes macOS ARM64 binaries; PyPI/uv delivery supports the expected
platform workflow. Linux ARM64 and macOS execution were **not tested**. Pure
Python pre-commit delivery does not imply all downstream hooks are portable.

OS package installation and existing Dev Container features can retain their own
configs. They do not have to be reimplemented in mise to use this result.

## Bazel and uv integration cost

The export probe emits the same native format that existing `rules_multitool`
registrations consume and Python metadata for the current shared launcher.
It was compared to existing metadata; no Bazel target was rebuilt from these
exported files. Version ownership transfers cleanly, but mise's native lock is
not a complete archive-installation recipe: Ruff's archive path is extra adapter
knowledge. Extending this bridge needs a documented recipe source/layout rule
per applicable archive pattern, registration generation/checks and an update
hook. Keep the bridge limited to simple existing tools; do not package complex
tools just to give them Bazel delivery.

With mise as the consumer interface, `mise install` plus `mise exec -- pre-commit`
needs mise bootstrap and its selected uv helper, but no separate Git-installed
Python runner. It therefore avoids adding a uv-only public execution adapter.

If #189 must specifically retain uv-only callers selecting our Git release,
export/package the maintained Python definitions for the existing runner. That
avoids duplicate maintained pins but retains the runner/package tests and a
small TOML/export boundary. uv itself does not natively read a remote mise config
to select our pre-commit pin. A bare `uvx pre-commit` would recreate the original
version drift. This is the unresolved interface decision, not a mise installer
limitation.

## Bootstrap, remaining guarantees and adoption signal

Downloaded mise **2026.10.24** through `gh release download`, verified SHA256
`be97dbac1c0b1fe08bd8c0cf01690f4273ea9aa02ad766b98d4e20c43eb9059d`
against the release SHASUMS256.txt, then ran it from `/tmp/score-mise-evaluation`.
Release-checksum comparison is not a separately authenticated publisher signature
verification. The probe isolates mise config/data/cache/state and uv caches;
no candidate was installed globally. A rerun requires that local mise binary.

Ruff's native hash lock does not lock all Python dependencies. The initial online
install and cached/direct invocations are not proof of ten-year artifact
retention or offline dependency completeness. Those upstream obligations need
explicit artifact retention/prefetch infrastructure. Disabling unexpected
execution-time auto-install in a production strict path also remains necessary.

The official [jdx/mise repository](https://github.com/jdx/mise) API reported
35,570 stars and activity on 2026-10-30 when inspected. This is a dated adoption
proxy, not a measured user count. Native [config environments](https://mise.jdx.dev/configuration/environments.html)
provide the profile mechanism tested here. No custom catalog schema was needed.
