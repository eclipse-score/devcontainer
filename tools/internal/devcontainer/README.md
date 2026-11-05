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

# Installing tools in DevContainers

The feature entry scripts and repository post-create script each request one
selection from [`environments.json`](../../environments.json):

| Selection | Caller |
| --- | --- |
| `s-core-local` | The published image's `s-core-local` feature |
| `bazel-feature` | The published image's `bazel-feature` feature |
| `repository-devcontainer` | This repository's post-create setup |

These lists record the existing callers' tool choices. A future image can add
its own selection. Base-image contents and external Dev Container features keep
their existing configuration owners; transitive packages are not listed here.
Bazel's public command targets are independent of these image selections.

```console
$ python3 tools/internal/devcontainer/install.py install-environment s-core-local
```

## Installation and permissions

One call validates the complete selection, adds temporary build packages,
installs tools and runs their setup, then removes the temporary packages.
Unknown names, missing direct dependencies and unavailable platform artifacts
fail before installation begins. A later download or installation failure stops
the sequence; installation is not transactional.

The installer uses `sudo` for system installation when needed and keeps npm in
the calling user's Node environment. Image builds already running as root
install directly. Python tools use the pinned uv and shared tool environments;
entrypoints in `/usr/local/bin` are available to all container users.

`--phase build|runtime|cleanup` requests an individual phase. `--providers`
restricts the installation methods applied. Native-, Python- and npm-only calls
skip APT build and cleanup steps. Writable native/Python destinations do not
require `sudo`. `--destination` and `--tool-dir` select these directories.
`--os` and `--cpu` select artifact metadata; they do not emulate apt or uv.

## Definitions and setup

| Group in a selection | Definition owner | Installation |
| --- | --- | --- |
| `native` | `lockfiles/*.lock.json` | Download and verify the release artifact |
| `python` | `providers.json` | Install the pinned Python package with uv |
| `apt` | `providers.json` | Install the declared packages using their version policy |
| `build-apt` | `providers.json` | Add temporary packages for build/setup; remove afterward |
| `npm` | `providers.json` | Install npm packages in the caller's environment |
| `setup` | `providers.json` | Run the declared tool-specific setup |

Definitions can name a script in [`setup/`](setup) with `setup_script`. This also
applies to APT tools: OpenJDK needs `java.sh` to configure `JAVA_HOME` after
installation. Each script explains its purpose and inputs at the top.
`install.py` passes metadata as environment variables, not command-line flags.
Scripts can query `selected ENVIRONMENT TOOL` and `items TOOL FIELD` for optional
bundle membership. CodeQL, for example, selects its C/C++ packs from the catalog
and declares zstd as a direct build dependency.

A child process cannot set variables in the shell that launched it. Java and
CodeQL therefore write profile files for later terminals. Feature tests use
`eval "$(.../install.py shell-metadata)"` to read quoted version assignments from
all catalogs in a single call.

## APT policies and platform limits

APT `distribution` follows Ubuntu's selected version; `prefix` includes any
Debian epoch (for example `1:3.22.0`); `package-name` chooses a versioned package
such as `python3.12`. Compatibility expectations for Git, Git LFS and gh are
separate from their unpinned APT requests. Black and other APT-provided Python
CLIs remain distribution-selected; migrating them to uv needs deliberate pins
and removal of the APT copies.

`packages` and `platforms` are independent lists. All listed packages are
installed on each supported host; apt selects the host build. Both QEMU guest
emulators, for example, are installed on both Linux host CPUs. CodeQL explicitly
omits Linux ARM64 because its selected bundle has no artifact for that platform.

`ca-certificates-java` populates Java's trust store from system certificates.
Pinning the helper alone would not freeze CA data or imported company CAs.
These inputs continue to follow distribution updates; this catalog does not
provide base-image, APT or certificate snapshots.

Removing a tool from a selection stops offering it in new setups. The installer
does not uninstall previous host copies. Return to the
[tool maintenance guide](../README.md) for adding commands and Bazel targets.
