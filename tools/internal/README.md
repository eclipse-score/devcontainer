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

`tools/owners/aqua/aqua.yaml` owns native releases and environment tags. Its
local recipes cover APM and starpls. `tools/owners/aqua/pyproject.toml` owns
Python distributions and versions. Root lockfiles, Python catalog versions,
repository membership, and the local facade metadata are generated outputs.

## Sources and runtime responsibilities

| Source | Owns |
| --- | --- |
| `tools/owners/aqua/aqua.yaml` and local registry recipes | Native release selections and environment tags |
| `tools/owners/aqua/aqua-checksums.json` | Generated checksums for selected native artifacts |
| `tools/owners/aqua/pyproject.toml` | Python direct versions and dependency groups |
| `tools/lockfiles/*.lock.json` | Portable URL/hash/layout snapshots for existing Bazel labels |
| `tools/score_tools/python_tools.bzl` | Python command identities and generated versions for Bazel and compatibility consumers |
| `tools/providers.json` | APT constraints, special release metadata, and external-provider lifecycle data |
| `tools/environments.json` | Feature and repository provider selections |
| Dev Containers configs and lockfiles | External feature selection, options, resolved versions, and OCI digests |
| `.bazelversion` | Workspace Bazel version, independent of image provisioning |

The feature Dockerfiles bootstrap checksum-pinned Aqua, copy the published
native selection directly, and install Python groups with the selected uv.
The generic root JavaScript/Node DevContainer provisions the repository
profile from its post-create command into the current user's stable prefix.
The helper records exposed command identities separately for each profile. A
reprovision removes a deselected command only when its path still matches the
recorded manager output and no other selected profile owns it. It preserves
foreign and user-replaced commands, and refuses to overwrite an untracked name
selected by Aqua or uv. A prefix without a supported ownership ledger needs a
fresh `--prefix`; the provisioner does not infer ownership from names. Both
paths retain APM's complete adjacent runtime directory. Runtime command
execution calls the installed binaries, not Aqua or uv.

Feature installers keep lifecycle, APT, and provider setup. Their
`install.py environment NAME` command applies APT/npm selection only; feature
scripts continue to configure Java, CodeQL packs, Bazel completion,
`bazel-compile-commands`, and other provider behavior. `install.py` retains
metadata, selection, version, and installed-state verification commands. It no
longer downloads native artifacts or installs Python tools.

## Host provisioning and execution

Provision the repository selection once into the default stable prefix:

```console
python3 tools/internal/devcontainer/provision_host_tools.py
```

The default prefix is `~/.local/share/score-tools`; pass `--prefix PATH` to
choose another location. Aqua's checksum-pinned bootstrap is installed under
that prefix only when a refresh is required. `--profile published` installs
the larger selection. `tools/run-tool --strict NAME ...` executes
`SCORE_TOOLS_BIN/NAME` directly. If that prepared host binary is unavailable,
the existing Bazel compatibility fallback remains. The direct route preserves
cwd, arguments, signals, and exit status without launching a manager, resolver,
or Bazel. Container calls prefer their image PATH and keep the same Bazel
fallback if a selected command is absent.

For normal `uv` and `uvx` commands in standalone host shells, add these exports
to the user's shell startup file after provisioning:

```sh
export SCORE_TOOLS_BIN="${HOME}/.local/share/score-tools/bin"
export PATH="${SCORE_TOOLS_BIN}:${PATH}"
```

The root DevContainer sets the same prefix in `remoteEnv`, so post-create
provisioning remains available to later integrated terminals and editor tasks.

Python Bazel targets continue to use the catalogued uvx executable. Ordinary
`uv` projects and `uvx --with` consumers keep standard package metadata and
extras; they do not need a custom consumer launcher. Existing native labels,
including APM and OpenCode, retain portable URL/hash/layout metadata. Complex
tools remain outside Bazel packaging.

## Local dependency wheel and release updates

Follow the maintained [local release and update workflow](aqua/README.md) for
owner refresh/check, explicit wheel identity/version, release validation, an
ordinary same-project uv/uvx update, native prefix reprovision, and the public
Bazel compatibility check. It records prerequisites, artifact handoff, and
recurring responsibilities. Hosting and public package identity remain open.

## Owner refresh and updates

After a Renovate update or an intentional owner edit, run:

```console
python3 tools/internal/aqua/refresh_owners.py
python3 tools/internal/aqua/sync_repository.py --check
python3 tools/internal/sync_readme.py --check
```

Renovate uses Aqua's pinned `aqua-renovate-config` preset for the live
`aqua.yaml`, Renovate's PEP 621 manager for dependency groups, and one narrow
custom manager for the Aqua bootstrap version in `aqua-bootstrap.toml`. Its
refresh command updates bootstrap artifact hashes first, then Aqua package
checksums and generated root metadata. Renovate ignores `experiments/**` so
historical configs, evidence and generated package copies do not become
additional owners. The daily job allowlists only
`python3 tools/internal/aqua/refresh_owners.py`; it never publishes a package
or image.

To add a standard-registry native CLI, add its exact version and intended tag
to `tools/owners/aqua/aqua.yaml`. Add a local registry recipe and policy entry
only when the pinned upstream registry lacks that package. Extend
`tools/internal/aqua/export_native.py` when its artifact name, archive layout,
or URL family differs from the supported mappings. For a Python CLI, add its
exact requirement to the intended dependency group and its public
package/entrypoint(s)/description identity to `tools/score_tools/python_tools.bzl`.
Refresh owners to derive versions, compatibility outputs, and tool docs.

APT providers remain in `tools/providers.json`. Keep feature-specific external
tools, npm packages and lifecycle duties with their established providers.

## Checks and interfaces

`tools/internal/devcontainer/install.py verify-environment NAME` checks
selected executable versions and installed Debian packages after image
construction. Existing Bazel labels preserve runner arguments, cwd and exit
behavior for consumers that explicitly use them.

```console
python3 -m unittest discover -s tools/tests -p 'test_*.py'
bazel test //tools:python_tool_runner_test //tools:run_tool_test
```

Native hashes identify portable artifacts. Aqua and Python dependency groups
own versions; root files generated from them are not additional version pins.
