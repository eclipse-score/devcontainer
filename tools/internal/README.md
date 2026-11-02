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

# Maintaining tools

The [mise release and update guide](mise/README.md) gives the supported owner
edit, refresh, local wheel handoff, independent uv/uvx update and native-prefix
reprovisioning sequence, including prerequisites and responsibility boundaries.

The tool catalog covers development commands, feature bundles, base images, and
build helpers. `tools/mise/*.toml` owns mise-managed tool versions; environment
compositions own selection. Native lockfiles and the Python Starlark catalog
remain generated compatibility outputs for Bazel and existing consumers.

## Sources and responsibilities

| Source | Owns |
| --- | --- |
| `tools/mise/mise.native.toml`, `mise.published.toml` | Native tool versions and the backend selected for each release |
| `tools/mise/mise.python.toml` | Exact PyPI command versions |
| `tools/mise/*.lock` | Resolved native release URLs and artifact hashes |
| `tools/lockfiles/*.lock.json` | Generated portable URLs, hashes, platforms and archive layouts for Bazel |
| `tools/score_tools/python_tools.bzl` | Generated Python distributions, exact top-level versions and entrypoints |
| `tools/providers.json` | APT constraints, special release setup metadata, compatibility expectations and references to external owners |
| `tools/environments.json` | Local feature and repository selections, including temporary build dependencies |
| Dev Containers configs and lockfiles | External feature selection, options, resolved feature versions and OCI digests |
| Dockerfiles / root Dev Containers config | Base images and trust-store refresh policy |
| `.bazelversion` | Workspace Bazel version, independent of the image's preinstalled version |

`score_tools.catalog` reads compatibility data without installation side effects.
The reader accepts only a literal Python-tool dictionary. Bazel loads the same
Starlark file during analysis; its runtime launcher carries immutable arguments
and the catalog-pinned uvx binary, so host Python is unnecessary.

The published image composes the s-core-local and bazel-feature selections.
Repository post-create uses its own selection. Their setup invokes the pinned
mise binary once to install selected commands under `/opt/score-tools/mise-data`
and creates direct links in `/usr/local/bin`. A per-bin ownership file records
which environments expose each link. Reprovisioning retires links removed from
that environment, retains links another environment still selects, and keeps
user replacements intact. Normal command execution invokes neither mise nor
Bazel. First setup must use a fresh bin directory; an existing selected
command without an ownership record causes setup to fail rather than guessing
who owns it.
Unrelated user commands remain untouched. Features still own lifecycle hooks,
mounts and special setup such as
JAVA_HOME, CodeQL packs and Bazel completion. APT, npm, external features and
provider metadata remain explicit inputs to `install.py`.

The yq download helper is removed: the existing image Python reads literal data
and emits quoted shell metadata. yq is therefore intentionally absent from the
shipped catalog. No new host Python requirement is introduced for Bazel callers.

## Maintenance

To add a native tool, add its exact backend/version to the appropriate mise
owner file, add environment membership, and add a backend-to-command mapping
only when it is not inferable. Run `tools/internal/mise/refresh.sh` to resolve
native artifacts and regenerate portable Bazel metadata. Existing multitool hubs
and aliases remain hand-maintained public interfaces; catalog validation checks
them against the generated definitions.

To add a Python tool, add its exact `pypi:` selection to `tools/mise/mise.python.toml`,
add its public identity/entrypoint/description to the literal Python catalog, and
select it in the environments that need it. Refresh generates the compatibility
version from mise. Bazel targets derive from the dictionary and the distribution
includes the file as package data. Ordinary uv/uvx consumers continue to resolve
these commands through the generated extras.

The [release and update guide](mise/README.md) owns the ordinary dependency-wheel
build/check and local handoff instructions. Generated extras and the release
manifest derive their pins from the native and Python owners; consumers use
them directly through uv or uvx. The check binds the release identity, current
owner pins, wheel digest and wheel metadata. Nothing is uploaded or registered.

To add an APT tool, define its packages and policy in `providers.json`, then add
its name to an environment's `apt` selection. Use `distribution` for intentionally
unpinned installs, `prefix` for Debian version-prefix constraints (including any
epoch), and `package-name` when the version selects the package identity.
Compatibility expectations are separate fields and do not masquerade as install
pins. Add tool-specific functional checks where package inspection is insufficient.

To update a tool, change its owning mise config. Renovate's daily job updates
the owner and runs `tools/internal/mise/refresh.sh`, which refreshes native
artifact locks, the Bazel/Python compatibility exports and the README inventory.
The same command works locally. It does not install or publish tools.

To remove a tool from an environment, remove that membership and reprovision
the same environment. Mise's ownership record removes only its now-unshared
link; links still used by another selection and user replacements are preserved.
Availability verification and generated membership use the same selection.
Deleting the global definition additionally removes its delivery targets and
registrations. Provider-specific lifecycle setup must be reviewed with the change.

```console
tools/internal/mise/refresh.sh
python3 tools/internal/mise/refresh.py --check
python3 tools/internal/sync_readme.py --check
python3 -m unittest discover -s tools/tests -p 'test_*.py'
bazel test //tools:mise_provision_test //tools:python_tool_runner_test //tools:run_tool_test
```

Host repository setup is explicit: run the following once, then commands resolve
directly from `/usr/local/bin`:

```console
sudo python3 tools/internal/mise/provision.py repository
```

`install.py environment repository` handles the selected
APT/npm providers. `install.py verify-environment NAME` inspects selected
executable versions and installed Debian package state and constraints; run it
as the development user. Feature tests additionally cover functionality,
compatibility and setup.

## Execution and migration

Direct Bazel targets select native artifacts or the Python definition through
pinned uvx. Native `<command>_binary` targets remain available as dependencies;
Python targets are for invocation, not hermetic Bazel actions.

`run-tool` retains container PATH precedence even with `--strict` and keeps
non-strict host PATH behavior. Strict host calls bypass arbitrary PATH entries,
use only symlinks into the mise install tree from `SCORE_TOOLS_BIN_DIR`,
`$HOME/.local/bin`, or `/usr/local/bin`, and fall back to the pinned Bazel target
when no provisioned link exists. A failed local non-strict invocation returns
its exit code and suggests strict execution; it does not silently retry.

Ordinary Python consumers use the checked dependency wheel's extras with uv
or uvx, as described in the [release and update guide](mise/README.md).
Consumers select the facade release, then run the real command without a SCORE
wrapper. Compatible uv and Python remain consumer prerequisites. The existing
`score-tool` entrypoint and root package are retained for compatibility; they
are not required by the ordinary wheel release path. Container and Bazel
delivery retain their catalog-pinned uv runtime.

## Guarantees

Native hashes verify exact artifacts. APT prefixes constrain direct package
versions without freezing repository state or transitive dependencies. Feature
OCI digests lock feature implementations, not every package those features fetch.
Python pins select direct distributions; interpreter and transitive resolution
are still uv's responsibility. Trust-store refresh and intentionally distribution
following tools remain unpinned. Full environment locking and reproducible image
rebuilds are outside this refactoring.
