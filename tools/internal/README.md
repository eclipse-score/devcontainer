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
| `tools/lockfiles/*.lock.json` | Define native tool versions and delivery metadata. |
| `tools/providers.json` | Define Python/npm packages, APT policies and special setup metadata. |
| `MODULE.bazel` | Makes native tool lockfiles available to `rules_multitool`. |
| `tools/BUILD.bazel` | Exposes public Bazel targets for each command. |
| Feature installers | Install the commands exposed on the DevContainer's `PATH`. |
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

Other package and setup definitions live in
[`providers.json`](../providers.json). Python commands declare their package,
version, console entrypoint and description there, alongside APT policies, npm
packages and feature-specific setup metadata. Native release artifacts keep
their multitool-compatible lockfiles.

The installer reads JSON directly. Bazel uses
[`catalog_repository.bzl`](../catalog_repository.bzl) to derive loadable Python
package data in its cache, so there is no second maintained Python catalog.
The existing feature installers and tests use `install.py shell-metadata` to
read quoted version/checksum variables without downloading yq. Their package
installation steps remain in the feature scripts.

APT `distribution` policies follow Ubuntu, while version prefixes retain Debian
epochs such as `1:3.22.0`. Executables omit that prefix when reporting their
version. CodeQL declares Linux x86_64 support and an explicit Linux ARM64
omission; the former macOS checksum is not a Linux ARM64 artifact.
`devcontainer-lock.json` continues to record external Dev Container features,
and `uv.lock.json` records the native installer runtime.

The published `score_devcontainer` Bazel module and DevContainer image share a
release version. Consumers using both must pin the same release.

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
4. Add the command to the appropriate feature installer:
   [`s-core-local/install.sh`](../../src/s-core-devcontainer/.devcontainer/s-core-local/install.sh)
   for general tools or
   [`bazel-feature/install.sh`](../../src/s-core-devcontainer/.devcontainer/bazel-feature/install.sh)
   for Bazel-specific tools.
5. Read the lockfile version and test the installed command in the matching
   feature test:
   [`s-core-local/tests/test_default.sh`](../../src/s-core-devcontainer/.devcontainer/s-core-local/tests/test_default.sh)
   or
   [`bazel-feature/tests/test_default.sh`](../../src/s-core-devcontainer/.devcontainer/bazel-feature/tests/test_default.sh).
6. Regenerate the documented command table:

   ```console
   $ python3 tools/internal/sync_readme.py
   ```

7. If this repository's own DevContainer needs the command, add it to
   [`.devcontainer/post_create_command.sh`](../../.devcontainer/post_create_command.sh).

For a Python command-line tool, add its definition to `tools/providers.json`
with `provider: "python"`, `package`, `version`, `entrypoint`, `description` and
`requires: ["uv"]`. Bazel targets are created for every Python definition
automatically. Add the command to each applicable DevContainer installer.
The Python package and console command may have different names.

Bazel executes the pinned package on demand with uvx; DevContainer installation
uses the same definition through uv. Add launcher and installer coverage to
`python_tool_runner_test` when either delivery contract changes.

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

The pre-commit hook runs the same command; pre-commit rejects the commit if
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
