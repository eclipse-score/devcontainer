<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Aqua repository integration — milestone 6

M5 retired the repository's native download/extract and Python installation
engine. M6 adds safe reused-prefix reconciliation and moves ordinary dependency
wheel generation and checks under maintained `tools/internal/aqua/` paths.
Root Bazel lockfiles, Python catalogs, environment selections, and tool
documentation remain generated compatibility outputs for existing consumers.

The published owner includes APM 0.35.0, OpenCode 2.2.3, starpls 0.1.22,
codespell 2.4.1, and the prior published tools. The repository owner includes
its established native set and pre-commit 4.7.0. Ordinary `uv` and `uvx`
consumers remain supported. APM uses a local aqua recipe and retains its full
expanded runtime tree because its executable loads adjacent files. OpenCode
uses the standard aqua registry at the exact selected 2.2.3 release. The
pinned registry lacks APM and starpls entries, so their declarative local
recipes and policy are maintained beside `aqua.yaml`.

## Owner refresh

Edit the production owners in [`tools/owners/aqua`](../../../tools/owners/aqua),
then run the single refresh path from the worktree root:

```sh
python3 tools/internal/aqua/refresh_owners.py
```

It refreshes aqua checksums, exports native metadata and Python selections to
the existing root interfaces, and regenerates the tool README. Renovate and
the daily allowed-command list invoke this same command. Aqua pins remain the
native version owners; Python dependency groups remain the Python version
owners. `aqua-bootstrap.toml` pins only the build-time aqua bootstrap and its
four supported artifact hashes.

## Runtime paths

The default S-CORE image build installs the `published` owner into
`/opt/score-tools`. It uses a checksum-verified temporary aqua bootstrap and
uv, then removes the bootstrap and owner inputs from the final image. Feature
installers continue to apply APT, npm, and external complex-tool setup. The
post-create step applies repository APT/npm providers and registers pre-commit.
Runtime tool calls use the installed image PATH; no manager or Bazel launch is
required.

On a host, provision one prefix with `tools/internal/devcontainer/provision_host_tools.py`:

```sh
python3 tools/internal/devcontainer/provision_host_tools.py \
  --profile repository --prefix "$HOME/.local/share/score-tools"
```

The provisioner installs its checksum-pinned Aqua bootstrap into that prefix
only when a refresh is required. `tools/run-tool --strict` calls the matching
executable directly from `SCORE_TOOLS_BIN` (defaulting to the prefix above). Existing
Bazel labels and runner arguments remain stable; their portable URLs, hashes,
versions, and archive layouts are generated from the same owners.

The host ownership ledger tracks each selected profile and the identity of each
exposed command. Reprovisioning removes only unchanged owned commands that no
current profile selects. Unknown prefixes need a fresh `--prefix`; foreign and
user-replaced commands are preserved.

The local dependency wheel uses a required explicit release version and
configurable package name. `uv` and `uvx` consume its ordinary optional
dependencies directly; the release remains local and unpublished.

See [README-m6.md](README-m6.md) for the maintenance ledger, exact checks,
remaining image/lifecycle gates, and platform limits. [README-m5.md](README-m5.md),
[README-m4.md](README-m4.md), and earlier milestone notes are historical.
