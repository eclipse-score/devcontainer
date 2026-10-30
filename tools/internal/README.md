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

The catalog covers development commands, feature bundles, base images, and build
helpers. Definitions own version decisions; environment compositions own selection.
The container installer is a consumer of those inputs, as are documentation and
verification. Standalone delivery imports no container installation code.

## Sources and responsibilities

| Source | Owns |
| --- | --- |
| `tools/lockfiles/*.lock.json` | Native releases, platforms, artifact hashes and layouts |
| `tools/score_tools/python_tools.bzl` | Python distributions, exact top-level versions and entrypoints |
| `tools/providers.json` | APT constraints, special release setup metadata, compatibility expectations and references to external owners |
| `tools/environments.json` | Local feature and repository selections, including temporary build dependencies |
| Dev Containers configs and lockfiles | External feature selection, options, resolved feature versions and OCI digests |
| Dockerfiles / root Dev Containers config | Base images and trust-store refresh policy |
| `.bazelversion` | Workspace Bazel version, independent of the image's preinstalled version |

`score_tools.catalog` reads these definitions without installation side effects.
The old `tools/lockfiles/python_tools.bzl` label remains a forwarding export
for Bazel consumers; it carries no separate pins. The reader accepts only a
literal Python-tool dictionary. Bazel loads that same Starlark
file during analysis; its runtime launcher carries immutable arguments and the
catalog-pinned uvx binary, so host Python is unnecessary.

The published image composes the s-core-local and bazel-feature selections.
Repository development uses its own selection and retains its Docker feature.
Features still own lifecycle hooks, mounts and special setup such as JAVA_HOME,
CodeQL packs and Bazel completion. They do not own another list of native or
Python commands. Python tools are installed to `/usr/local/bin` with environments
under `/usr/local/share/uv/tools`, accessible to the development user. Bazel setup
uses the Dev Containers `_REMOTE_USER`, defaulting to vscode.

The yq download helper is removed: the existing image Python reads literal data
and emits quoted shell metadata. yq is therefore intentionally absent from the
shipped catalog. No new host Python requirement is introduced for Bazel callers.

## Maintenance

To add a native tool, define its lockfile and add the relevant environment
membership. Register its multitool hub and Bazel aliases; catalog validation
checks both explicit registrations against all native definitions.

To add a Python tool, edit the literal dictionary and select its environments.
Bazel targets derive from the dictionary and the distribution includes the file
as package data. There is no second package requirements file to update.

To add an APT tool, define its packages and policy in `providers.json`, then add
its name to an environment's `apt` selection. Use `distribution` for intentionally
unpinned installs, `prefix` for Debian version-prefix constraints (including any
epoch), and `package-name` when the version selects the package identity.
Compatibility expectations are separate fields and do not masquerade as install
pins. Add tool-specific functional checks where package inspection is insufficient.

To update a tool, change its owning definition, refresh native artifact hashes
where relevant, and regenerate the overview. Existing Renovate release managers
continue to edit native lockfiles; duplicate apm/opencode YAML managers are removed.
Other providers currently require the manual review named in the overview.

To remove a tool from an environment, remove that membership. Installation,
availability verification and generated membership use that same selection.
Deleting the global definition additionally removes its delivery targets and
registrations. Provider-specific lifecycle setup must be reviewed with the change.

```console
python3 tools/internal/sync_readme.py
python3 tools/internal/sync_readme.py --check
python3 -m unittest discover -s tools/tests -p 'test_*.py'
bazel test //tools:python_tool_runner_test //tools:run_tool_test
```

`install.py verify-environment NAME` inspects selected executables' reported
versions and installed Debian package state and constraints. Run it as the
actual development user. It emits observed versions separately from requested
policy. Feature tests additionally cover functionality, compatibility and setup.

## Execution and migration

Direct Bazel targets select native artifacts or the Python definition through
pinned uvx. Native `<command>_binary` targets remain available as dependencies;
Python targets are for invocation, not hermetic Bazel actions.

`run-tool` retains existing behavior: container PATH wins even with `--strict`;
non-strict host invocation prefers PATH; strict host invocation uses Bazel.
A failed local invocation returns its exit code and suggests strict execution;
it does not silently retry. PATH selection is not a version guarantee and a
container marker is not an image attestation. This compatibility decision avoids
changing downstream hooks during the catalog refactoring.

The new explicit `score-tool` entrypoint selects Python tools through caller uv.
It preserves cwd, argument boundaries, signals and exit status using exec.
Future release-based consumer usage (replace RELEASE with a published Git ref):

```console
uvx --from 'git+https://github.com/eclipse-score/devcontainer.git@RELEASE' score-tool pre-commit run --all-files
```

For local verification, use `git+file:///absolute/path/to/repository@COMMIT` from
outside the checkout. No package or image publication is needed. Consumers may
migrate unpinned `uvx pre-commit` calls to this explicit release-selected form.
The standalone path requires compatible uv already on PATH and does not pin or
bootstrap it. Container and Bazel delivery retain their catalog-pinned uv runtime.

## Guarantees

Native hashes verify exact artifacts. APT prefixes constrain direct package
versions without freezing repository state or transitive dependencies. Feature
OCI digests lock feature implementations, not every package those features fetch.
Python pins select direct distributions; interpreter and transitive resolution
are still uv's responsibility. Trust-store refresh and intentionally distribution
following tools remain unpinned. Full environment locking and reproducible image
rebuilds are outside this refactoring.
