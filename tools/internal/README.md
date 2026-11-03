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

# Maintaining command-line tools

This guide describes how the pinned command-line tools are provided and
maintained. For normal usage, see [Pinned command-line tools](../README.md).

The approach complements the general direction in
[DR-001 Infrastructure Design Decision](https://eclipse-score.github.io/score/main/design_decisions/DR-001-infra.html).

## Delivery contract

One catalog is delivered through two execution paths:

| Component | Responsibility |
| --- | --- |
| `tools/lockfiles/*.lock.json` and `tools/lockfiles/python_tools.bzl` | Define versions and delivery metadata. |
| `MODULE.bazel` | Makes native tool lockfiles available to `rules_multitool`. |
| `tools/BUILD.bazel` | Exposes public Bazel targets for each command. |
| `tools/providers.json` | Define APT policies, npm packages and special feature setup metadata. |
| `tools/environments.json` | Record the complete tool selection of each existing setup caller. |
| Feature installers | Apply selections and install the commands exposed on the DevContainer's `PATH`. |
| `tools/run-tool` | Uses the command on `PATH` in a container or locally when available; otherwise uses the public Bazel alias (`--strict` forces Bazel). |
| `tools/README.md` | Documents every command and its version from the catalog. |

A command is available when its catalog metadata, Bazel target, and applicable
DevContainer installer are registered together. The runner selects between
those delivery paths; the catalogs remain the command registries.

## Architecture

The public interface is `.devcontainer/run-tool` in each consumer
repository. Inside a container or on the host, it uses the command on `PATH`
when available, or falls back to Bazel (`--strict` forces Bazel). Developers
use the same command line without choosing the execution path.

![Command-line tool delivery](tool-delivery.svg)

Native tools with upstream release artifacts use
[`rules_multitool`](https://github.com/bazel-contrib/rules_multitool).

The `multitool_aliases` helper exposes the `rules_multitool` `cwd` target as
the public command. That wrapper restores `BUILD_WORKING_DIRECTORY` before
starting a tool, so configuration discovery and repository-relative paths
behave like a direct invocation.

Python packages do not provide the platform-specific, checksum-addressed
release binaries expected by `rules_multitool`. Their public Bazel targets
therefore use the `uvx` binary from `rules_multitool` to create an isolated
environment for the exact catalogued package version. A shell launcher restores
the caller's working directory before invoking `uvx`; using shell here is
intentional so Python-based tools do not require a system Python installation
on the host.

The DevContainer takes the other delivery path: it installs each Python tool
once with the catalogued `uv` binary and exposes the resulting entrypoint on
`PATH`. Python is already part of the image before feature tools are installed,
so the installer can use its standard library without adding a container or
host dependency.

The maintained runner source is [`run-tool`](../run-tool). It remains under
`tools/` in this implementation repository; consumer repositories copy it to
`.devcontainer/run-tool`. This repository invokes that source directly from
its pre-commit configuration. Consumer documentation only presents the copied
`.devcontainer/run-tool` path.

## Sources of truth

Native tool metadata lives in
[`tools/lockfiles/*.lock.json`](../lockfiles). Each lockfile records versions,
supported platforms, download URLs, checksums, and archive layouts.
`rules_multitool` consumes the files for Bazel. The standard-library-only
[`catalog.py`](catalog.py) reads metadata for
[`devcontainer/install.py`](devcontainer/install.py) and README generation.
The reader has no installation side effects; download, platform selection,
and installation remain in the container installer.
Other direct packages and special setup are defined in
[`providers.json`](../providers.json): APT constraints, npm package identities,
Bazel preinstallation and CodeQL metadata. The selections reference these names
without copying their versions.

Python command-line tool metadata lives in
[`tools/lockfiles/python_tools.bzl`](../lockfiles/python_tools.bzl). The file is
a data-only Starlark dictionary because Bazel must read the pin during analysis,
before the command can run. Its restricted literal form is also valid Python
syntax. During DevContainer setup, `install.py` runs as root so it can install
tools in system locations such as `/usr/local/bin`. The shared reader parses
the catalog with `ast.literal_eval` instead of executing it as Python, so
catalog changes can provide only literal data and cannot run code with the
installer's privileges.
This shared format keeps the package, console entrypoint, version, and
description in one source of truth while Bazel execution remains independent
of host Python.

APT `distribution` policies intentionally follow the distribution, `prefix`
constraints include Debian epochs, and `package-name` selects a versioned package
name (for example `python3.12`). Compatibility expectations for Git, Git LFS and
gh remain separate from their unpinned APT requests. The installer passes version variables directly to its setup subprocesses.
Feature tests use `shell-metadata` to read quoted assignments in their own shell;
there is no separate loader script or downloaded parser.

The catalogs have distinct ownership: `devcontainer-lock.json` records external
DevContainer features, `python_tools.bzl` records Python package releases, and
`uv.lock.json` records the installer runtime. Each version is therefore owned
by the component that resolves it.

The published `score_devcontainer` Bazel module and DevContainer image share a
release version. Consumers using both must pin the same release.

## Tool selections and image variants

Definitions answer **which version and installation method?** Named selections
in [`tools/environments.json`](../environments.json) answer **which tools belong
here?** Image and feature setup determines the base OS and lifecycle.
Selections contain names, not another copy of versions or download metadata.

| Selection | Existing caller |
| --- | --- |
| `s-core-local` | The published image's `s-core-local` feature |
| `bazel-feature` | Its `bazel-feature` feature |
| `repository-devcontainer` | This repository's post-create setup |

These names identify the current callers and their historical tool membership;
they are not newly designed tool groups. The published image combines the first
two through its existing features. A future lean CI image can define its own
selection based on the jobs it needs to run. This does not add another image.

Each selection groups its tools by installation method:

| Group | Definition owner | Applied by |
| --- | --- | --- |
| `native` | `lockfiles/*.lock.json` | The native downloader |
| `python` | `lockfiles/python_tools.bzl` | Catalogued uv, with system-wide entrypoints |
| `apt` | `providers.json` | apt, preserving package/version policy and recommendations |
| `build-apt` | `providers.json` | apt during build; removed during cleanup |
| `npm` | `providers.json` | npm in the appropriate user's environment |
| `setup` | `providers.json` | Setup scripts declared by `setup_script`, gated by membership |

For example, the local feature applies its selected groups during setup:

```console
$ python3 tools/internal/devcontainer/install.py install-environment s-core-local --phase build
$ python3 tools/internal/devcontainer/install.py install-environment s-core-local
# Declared setup runs during installation, then temporary packages are removed:
$ python3 tools/internal/devcontainer/install.py install-environment s-core-local --phase cleanup
```

The repository setup applies `npm` as the development user and `native python`
with sudo, using `--providers`. This preserves the Node base image's npm access
while putting Python commands in system paths. The feature's pre-commit,
basedpyright and pytest use `/usr/local/bin` and shared uv tool environments;
all container users can access them. Package versions are unchanged.

`--destination`, `--os` and `--cpu` retain their native-install meanings.
APT/setup platform declarations are also checked; `--os` and `--cpu` select
metadata, not an emulated runtime for apt or uv. The whole selection is checked
before applying any phase: unknown names, wrong provider groups, missing direct
dependencies and unsupported platform artifacts fail before installation.
CodeQL's existing Linux ARM64 omission is explicit. Download or installation
failure can still leave earlier tools installed; application is not transactional.

Feature entry scripts only apply the selection's build, runtime and cleanup
phases. Tool-specific steps live in `internal/devcontainer/setup/`; definitions
name the required script with `setup_script`. For example, `openjdk` selects an
APT package and declares Java home configuration. Its name carries no version;
`packages` and `version` select the actual OpenJDK release.

The installer gives setup scripts version variables directly as their process
environment. Python can set a child's environment, but cannot change the shell
that invoked it. Java and CodeQL setup therefore also write profile files for
later terminals. The feature tests read quoted `shell-metadata` output directly.

Setup scripts can query `selected ENVIRONMENT TOOL` for optional bundle members.
CodeQL pack names come from the owned bundle through `items`, not a second list.
CodeQL declares `zstd` as a build dependency, so missing decompression support is
rejected before the build phase. Removing membership stops new setup from
offering the tool; it does not uninstall existing host copies.

For APT definitions, `packages` and `platforms` are independent lists. Every
listed package is installed on each supported host; apt selects its host build.
For example, both QEMU guest emulators are installed on both Linux host CPUs.
Their order does not map packages to architectures.

A distribution policy is not an exact pin: Black and the other APT-provided
Python CLIs retain the current Ubuntu version selection. Changing their provider
to pinned uv distributions requires explicit version choices and removal of the
APT copies. It is a separate change from recording existing selections.

`ca-certificates-java` builds the Java trust store from system certificates.
Pinning that helper alone does not freeze the trust data or imported corporate
CAs. These continue to receive distribution updates. Reproducible base/APT and
certificate snapshots, and rebuilding releases for trust updates, are outside
this change's guarantee.

This file covers the direct tools managed by our three setup scripts. Base-image
contents, external Dev Container features (such as LLVM, common-utils and DinD),
and their options and locks retain their existing configuration owners. It is
not an inventory of transitive packages, editor extensions or image contents.

## Adding or updating a tool

For a tool distributed as a native release artifact, make the following
changes together:

1. Add or update the multitool-compatible
   `tools/lockfiles/<command>.lock.json`, including a `description` field
   for each tool entry (used to generate the README table).
2. Register the lockfile with `multitool.hub` in the root
   [`MODULE.bazel`](../../MODULE.bazel).
3. Add `multitool_aliases("<command>")` to
   [`tools/BUILD.bazel`](../BUILD.bazel).
4. Add the command to the applicable native selection in
   [`tools/environments.json`](../environments.json): `s-core-local` for the
   `s-core-local` feature or `bazel-feature` for the `bazel-feature` feature.
5. Read the lockfile version and test the installed command in the matching
   feature test:
   [`s-core-local/tests/test_default.sh`](../../src/s-core-devcontainer/.devcontainer/s-core-local/tests/test_default.sh)
   or
   [`bazel-feature/tests/test_default.sh`](../../src/s-core-devcontainer/.devcontainer/bazel-feature/tests/test_default.sh).
6. Regenerate the documented command table:

   ```console
   $ python3 tools/internal/sync_readme.py
   ```

7. If this repository's own DevContainer needs the command, add it to the
   `repository-devcontainer` selection in `tools/environments.json`.

For a Python command-line tool, add an entry to
`tools/lockfiles/python_tools.bzl`, add `python_tool("<command>")` to
`tools/BUILD.bazel`, and add its name to the `python` group of each applicable
selection in `tools/environments.json`. Keep the catalog as a single literal
`PYTHON_TOOLS` assignment: this is what makes it safe for the installer and
directly loadable by Bazel. The `package` selects the distribution passed to
`uv`, while `entrypoint` names the console command because those names need not
be identical.

Bazel invokes Python tools on demand with the pinned `uvx`; DevContainers
install the same package with the pinned `uv`. A Python selection must also
select native `uv`; Bazel already carries pinned uvx in its launcher runfiles. Add launcher and installer
coverage to `python_tool_runner_test` when either delivery contract changes.

Keep related commands such as `uv` and `uvx` in one lockfile when upstream
publishes them together. The installer can locate a command in a differently
named lockfile, but an explicit `--lockfile` remains available for ambiguous
cases.

To remove a command, remove it from the same integration points, including
its `description` field. Then run `sync_readme.py` (see below); it rejects
lockfile entries without a description.

## Validation and release alignment

Regenerate the user-facing command table after changing a lockfile or a
description:

```console
$ python3 tools/internal/sync_readme.py
```

The pre-commit hook also validates selection names, provider groups, direct
dependencies and tool references.
It runs the same command; pre-commit rejects the commit if
running it changes `tools/README.md`, so a stale table cannot be committed.

Run the feature test for every installer changed. The feature tests read their
expected versions from the catalog, which verifies that the DevContainer and
lockfiles remain aligned. Publish the Bazel module and the DevContainer image
with the same release version so consumer repositories can pin one version for
both delivery paths.

`python_tool_runner_test` uses a fake uv executable to verify arguments,
environment variables, and working-directory behavior without network access.
CI additionally runs the real `//tools:pre-commit` target as a smoke test
because only that target exercises `rules_multitool`, Bazel runfiles, and uvx
together.

Run the shared reader and README regression tests with the image's Python
(no additional packages or installation needed):

```console
$ python3 -m unittest discover -s tools/tests -p '*_test.py'
```

The scripts locate the shared internal reader relative to their own files, so they also work
from another working directory and in the image's copied `tools` directory.
Ordinary imports from the repository use `tools.internal.catalog`.

## Bazel target conventions

`multitool_aliases` exposes two native-tool targets:

- `<command>` uses the caller's working directory and is intended for
  `bazel run`.
- `<command>_binary` is the raw executable for use as a tool dependency in other
  Bazel rules.

Python tools expose only the runnable `<command>` target. They are intended for
interactive and CI use, not as executable dependencies in Bazel actions. The
target embeds the catalog metadata as arguments to a shell launcher and carries
only the pinned `uvx` executable in its runfiles, which keeps execution
independent of host Python and avoids runtime catalog path resolution.

`rules_shell` supplies the `sh_binary` and `sh_test` APIs consistently across
the supported Bazel generations, so one BUILD definition serves every
supported consumer.

## Rationale and boundaries

The runner supports mixed workflows without exposing two user interfaces. A
container-only implementation would not cover developers who do not run the
DevContainer at all, while arbitrary system-installed tools would lose
version alignment with those who do.

Full Bazel toolchains remain appropriate for tools that participate in build
actions or platform transitions. They add unnecessary complexity for the
standalone CLIs covered here. Bazel targets, exported lockfiles, and
`internal/devcontainer/install.py` are implementation details; the runner is
the only documented consumer invocation method.
