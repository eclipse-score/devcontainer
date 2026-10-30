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

# Tooling status quo

Snapshot of repository configuration at commit `0cc738794384cf32f08ba616c049bf8f3fb7124c`
(2026-10-30), supporting [#190](https://github.com/eclipse-score/devcontainer/issues/190).
This is an inventory of existing behavior, not the target architecture or a
generated package manifest. Versions below describe source configuration;
they were not obtained by building or inspecting a container image.

The inventory covers explicitly configured development tools, installation
helpers, and their delivery paths. It does not enumerate every package inherited
from base images, external features, or transitive dependencies. A Bazel target
below means a public CLI target in this repository, not that the tool is
unavailable through other Bazel modules.

## Two different containers

| Container | Definition | Purpose |
| --- | --- | --- |
| Published S-CORE image | [`src/s-core-devcontainer/.devcontainer/devcontainer.json`](../src/s-core-devcontainer/.devcontainer/devcontainer.json) | Development environment delivered to consuming repositories. Uses `buildpack-deps:noble-curl`, external features, and two local features. |
| Repository development container | [`.devcontainer/devcontainer.json`](../.devcontainer/devcontainer.json) | Builds and tests the published image. Uses `mcr.microsoft.com/devcontainers/javascript-node:4-24`, Docker-in-Docker, and a post-create script. |

The tables below describe the published image unless stated otherwise. Its
Dockerfile copies all of `tools/` to `/usr/local/share/score-tools`; feature
installers call the Python installer from that location.

## Native tools in the shared catalog

Each row has a definition in [`tools/lockfiles/`](../tools/lockfiles/), including
version, download URLs, SHA256 hashes, supported platforms, and extraction layout.
The container uses [`install.py install`](../tools/internal/devcontainer/install.py)
to install into `/usr/local/bin` as root. The commands are available to the
development user. For directory archives, the installer also copies the archive's
supporting files into that destination.

[`MODULE.bazel`](../MODULE.bazel) registers each lockfile with `rules_multitool`.
[`tools/BUILD.bazel`](../tools/BUILD.bazel) separately registers public targets
through [`multitool_aliases`](../tools/multitool.bzl): `<command>` restores the
caller's working directory, and `<command>_binary` exposes the raw executable.

| Command | Version | Lockfile | Container feature | Public Bazel CLI target |
| --- | --- | --- | --- | --- |
| `actionlint` | 1.7.7 | `actionlint.lock.json` | s-core-local | `//tools:actionlint` |
| `apm` | 0.35.0 | `apm.lock.json` | s-core-local | `//tools:apm` |
| `bazelisk` | 1.27.0 | `bazelisk.lock.json` | bazel-feature | `//tools:bazelisk` |
| `buildifier` | 8.2.1 | `buildifier.lock.json` | bazel-feature | `//tools:buildifier` |
| `opencode` | 2.2.3 | `opencode.lock.json` | s-core-local | `//tools:opencode` |
| `ruff` | 0.11.13 | `ruff.lock.json` | s-core-local | `//tools:ruff` |
| `shellcheck` | 0.10.0 | `shellcheck.lock.json` | s-core-local | `//tools:shellcheck` |
| `starpls` | 0.1.22 | `starpls.lock.json` | bazel-feature | `//tools:starpls` |
| `uv` | 0.13.6 | `uv.lock.json` | s-core-local | `//tools:uv` |
| `uvx` | 0.13.6 | `uv.lock.json` | s-core-local | `//tools:uvx` |
| `yamlfmt` | 0.17.0 | `yamlfmt.lock.json` | s-core-local | `//tools:yamlfmt` |

All these lockfiles include Linux x86_64, Linux arm64, and macOS arm64 artifacts.
Only `apm` and `opencode` additionally include macOS x86_64. There are no Windows
artifacts in this catalog.

## Python tools

The Python interpreter and Python CLIs have three different installation paths.
Ruff is delivered as a native artifact and is listed above.

| Tool or package | Version source | Installation and location | Public Bazel CLI target |
| --- | --- | --- | --- |
| `pre-commit` | [`python_tools.bzl`](../tools/lockfiles/python_tools.bzl): 4.7.0, package and entrypoint both `pre-commit` | `install.py install-python` invokes `uv tool install --force pre-commit==4.7.0` as root; explicit `UV_TOOL_BIN_DIR=/usr/local/bin`, `UV_TOOL_DIR=/usr/local/share/uv/tools` | `//tools:pre-commit` |
| `basedpyright` | s-core-local `versions.yaml`: 1.35.0 | Separate `uv tool install basedpyright@...` under the user selected by `su $(ls /home)`; user-level uv defaults, no explicit destination | None |
| `pytest` | s-core-local `versions.yaml`: 9.0.2 | Separate `uv tool install pytest@...` under the same user; user-level uv defaults, no explicit destination | None |
| Python interpreter | s-core-local `versions.yaml`: `3.12` | APT package selection `python${python_version}`; no exact Debian package revision, system installation | None |
| `python3-pip`, `python3-venv` | APT repositories at build time | APT, no explicit package versions, system installation | None |
| `flake8`, `python3-autopep8`, `black`, `python3-yapf`, `mypy`, `pydocstyle`, `pycodestyle`, `bandit`, `pipenv`, `virtualenv`, `pylint` | APT repositories at build time | APT, no explicit package versions, system installation | None |

Sources: [s-core-local installer](../src/s-core-devcontainer/.devcontainer/s-core-local/install.sh)
and [version declarations](../src/s-core-devcontainer/.devcontainer/s-core-local/versions.yaml).
APT owns package layouts, typically placing commands under `/usr/bin`; these
paths are not selected by the shared tool installer.

`python_tools.bzl` currently contains only `pre-commit`. It is a literal Starlark
dictionary loaded directly by Bazel and parsed with `ast.literal_eval` by the
container installer. The installer validates a single `PYTHON_TOOLS` assignment
rather than executing the catalog as Python.

The Bazel [`python_tool` macro](../tools/python_tool.bzl) embeds the catalog's
`package==version` and entrypoint in a shell launcher. That
[launcher](../tools/internal/run_python_tool.sh) restores the caller's working
directory and executes the catalog-pinned `uvx` binary. No host Python is required
to start the Bazel target. There is no corresponding `<command>_binary` target
for Python tools.

The Python catalog fixes top-level package versions, not transitive dependencies,
Python interpreter versions, or wheel hashes. The repository does not ship a
Python environment lockfile for these tool installations. Container and Bazel
therefore share the `pre-commit` package pin, but not a fully specified environment.

## Other tools installed by local features

These tools have no public CLI target in `tools/BUILD.bazel`.

| Tool or package | Declared version | What controls installation | Location / user |
| --- | --- | --- | --- |
| Graphviz | 2.42.2 | s-core-local YAML, APT `graphviz=${graphviz_version}*` | System APT installation |
| Protobuf compiler (`protoc`) | 3.21.12 | s-core-local YAML, APT version prefix | System APT installation |
| `git` | 2.43.0 | **YAML value is only checked by tests**; installer runs unversioned `apt-get install git` | System APT installation |
| `git-lfs` | 3.4.1 | **YAML value is only checked by tests**; installer runs unversioned `apt-get install git-lfs` | System APT installation |
| GitHub CLI (`gh`) | 2.45.0 | **YAML value is only checked by tests**; installer runs unversioned `apt-get install gh` | System APT installation |
| OpenJDK 21 | 21.0.12 | s-core-local YAML, APT version prefix for `openjdk-21-jdk-headless`; `ca-certificates-java` unversioned | System installation; `JAVA_HOME` written to `/etc/profile.d/java_home.sh` |
| QEMU ARM and x86 system emulators | `1:8.2.2` | s-core-local YAML, APT version prefixes for `qemu-system-arm` and `qemu-system-x86` | System APT installation |
| `sshpass` | 1.09 | s-core-local YAML, APT version prefix | System APT installation |
| `gdb` | 15.0.50 | s-core-local YAML, APT version prefix | System APT installation |
| `valgrind` | 3.22.0 | s-core-local YAML, APT `1:${valgrind_version}*` | System APT installation |
| `ripgrep` (`rg`) | 14.1.0 | s-core-local YAML, APT version prefix | System APT installation |
| `lcov` | 2.0 | s-core-local YAML, APT version prefix | System APT installation |
| `pkg-config` | 1.8.1 | s-core-local YAML, APT version prefix | System APT installation |
| `libcairo2-dev` | 1.18.0 | s-core-local YAML, APT version prefix; headers for Python Cairo builds | System APT installation |
| CodeQL | 2.21.4 | s-core-local YAML, explicit bundle download and architecture-specific SHA256 | `/usr/local/codeql`, command linked into `/usr/local/bin`; installed on Linux amd64, skipped on Linux arm64 |
| CodeQL coding-standard packs | 2.54.0 | s-core-local YAML, four explicit `codeql pack download` calls: MISRA C++, MISRA C, CERT C++, CERT C | `/usr/local/codeql/qlpacks` |
| Bazel | 8.6.0 preinstalled | bazel-feature YAML sets `USE_BAZEL_VERSION` during preinstallation through Bazelisk; consumer workspace can select another version | `/usr/local/bin/bazel` links to Bazelisk; Bazel downloaded under the development user's home |
| `bazel-compile-commands` | 0.18.0 | bazel-feature YAML, downloaded `.deb` selected by Ubuntu codename and architecture, verified against SHA256 | System `.deb` installation |

Sources: [s-core-local installer](../src/s-core-devcontainer/.devcontainer/s-core-local/install.sh),
[bazel-feature installer](../src/s-core-devcontainer/.devcontainer/bazel-feature/install.sh),
and [bazel-feature versions](../src/s-core-devcontainer/.devcontainer/bazel-feature/versions.yaml).
The repository also has a [`.bazelversion`](../.bazelversion) of 8.6.0 for its own
workspace. The feature's
[startup helper](../src/s-core-devcontainer/.devcontainer/bazel-feature/install_matching_bazel_version.sh)
handles workspaces with a different `.bazelversion`.

APT version prefixes allow multiple package revisions and depend on repository
availability. They do not lock the complete dependency closure or use an APT
repository snapshot.

## External features and installation helpers

| Component | Version source / behavior | Scope |
| --- | --- | --- |
| LLVM feature | Published-image `devcontainer.json` requests LLVM `20`; its lockfile pins feature 3.2.0 by OCI digest | Tool installation delegated to the feature; image tests independently expect Clang, clangd, clang-format, and clang-tidy 20.1.8 |
| common-utils feature | Published-image lockfile pins feature 2.5.4 by OCI digest; `upgradePackages=false` | User and general environment setup; package selection delegated to the feature |
| YAML loader (`yq`) | [`load_feature_versions.sh`](../tools/internal/devcontainer/load_feature_versions.sh) hardcodes v4.47.2 and amd64/arm64 SHA256 values | Downloads a temporary executable to read feature YAML, then removes it; also invoked by feature tests |
| CA certificates | Published-image Dockerfile explicitly installs without a version and refreshes the trust store | System trust store |
| Man pages | s-core-local installer runs `unminimize` and installs `man-db`, `manpages`, `manpages-dev`, `manpages-posix`, `manpages-posix-dev` without versions | System documentation |
| Build helpers | Local features install `apt-transport-https`; s-core-local additionally installs `zstd` for extraction; both are removed during cleanup | Build-time dependencies |
| Repository devcontainer base and Docker-in-Docker | [Root devcontainer configuration](../.devcontainer/devcontainer.json) selects image tag `4-24` and feature major `4`; [root lockfile](../.devcontainer/devcontainer-lock.json) records feature resolution | Separate repository development environment |
| Dev Containers CLI | Root [post-create script](../.devcontainer/post_create_command.sh) runs `npm install -g @devcontainers/cli`, without a version | Repository development container |

The root post-create script also installs `actionlint`, `bazelisk`, `buildifier`,
`ruff`, `shellcheck`, `uv`, `uvx`, and `yamlfmt` from the native catalog, then
`pre-commit` from the Python catalog into the explicit system-wide uv directories.
It registers pre-commit hooks and creates a Docker builder. That tool selection is
another manually maintained list, separate from the published-image features.

## Execution and version selection

[`tools/run-tool`](../tools/run-tool) is copied into consuming repositories as
`.devcontainer/run-tool`. It does not load the catalog itself:

1. In a detected container, an available command on PATH is executed directly,
   including when `--strict` is set.
2. Outside that branch, an available PATH command is preferred unless `--strict`
   is set. Its version is not checked. A failure is reported with a suggestion to
   use `--strict`; it does not automatically retry through Bazel.
3. Otherwise, an available `bazel` runs
   `@score_devcontainer//tools:<command>`. Without it, execution fails.

Container detection checks `/.dockerenv`, `/run/.containerenv`, or `/devcontainer`;
it does not establish which image or release is running. Neither the container
branch nor the host PATH branch verifies that the executable matches a catalog
pin. Bazel resolves the tool from the module release selected by the consumer.

There is no standalone Python package exposing the catalog through uv in this
snapshot. That is the proposed additional delivery path in
[#189](https://github.com/eclipse-score/devcontainer/issues/189).

## Documentation, tests, and dependency updates

| Component | Current coverage / dependency |
| --- | --- |
| Generated tool table | [`tools/README.md`](../tools/README.md) lists native JSON entries and the Python catalog; excludes APT tools, feature-provided tools, `pytest`, and `basedpyright`. [`sync_readme.py`](../tools/internal/sync_readme.py) imports catalog functions from the container installer. |
| Feature tests | [s-core-local tests](../src/s-core-devcontainer/.devcontainer/s-core-local/tests/test_default.sh) and [Bazel tests](../src/s-core-devcontainer/.devcontainer/bazel-feature/tests/test_default.sh) read JSON/Python pins through `install.py` and other expected versions through feature YAML. Individual checks and tool lists are handwritten. |
| Python assertions | Some tools receive only execution checks. The Black check greps the Python version, not a pinned Black release. The pycairo source-install test independently hardcodes `pycairo==1.29.0`; pycairo is not installed by the image feature. |
| Outer image tests | [`test-project/test.sh`](../src/s-core-devcontainer/test-project/test.sh) hardcodes LLVM tool expectations, sources both local feature tests, and checks the trust store and environment. |
| Runner tests | [`run_tool_test`](../tools/tests/run_tool_test.sh) covers selection behavior; [`python_tool_runner_test`](../tools/tests/python_tool_runner_test.sh) uses a fake uv executable to check launcher/installer arguments, environment, and working directory. |
| CI | [PR CI](../.github/workflows/ci.yaml) runs pre-commit in the repository development container, the two Bazel contract tests, a real `//tools:pre-commit --version` smoke test, and image build/tests for amd64 and arm64. |
| Pre-commit configuration | [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) routes local format/lint hooks through `tools/run-tool`, invokes Bazelisk directly for module checks, and runs README synchronization. Remote hooks have separate pinned revisions. |
| Renovate | [Configuration](../.github/renovate.json5) enables only custom regex managers: `apm`, `opencode`, and `uv` JSON versions, plus `apm`/`opencode` YAML versions. The [daily workflow](../.github/workflows/daily.yml) enables its runner and allows post-upgrade digest refresh and README synchronization. No manager here covers `python_tools.bzl` or the other feature YAML tool versions. |
| Dependabot | [Configuration](../.github/dependabot.yml) covers GitHub Actions, Docker under `src/s-core-devcontainer/.devcontainer`, and Dev Containers at the repository root. It does not configure Python catalog updates or published-image feature updates under `src/`. |

## Observed duplication and maintenance boundaries

- `apm` and `opencode` versions remain in s-core-local YAML as well as their JSON
  lockfiles. Installation and feature assertions use the JSON values; the YAML
  values are unused by those paths. Renovate still targets both copies.
- `git`, `git-lfs`, and `gh` YAML values are test expectations, not installation
  constraints. Their apparent pins do not control APT selection.
- Bazel's preinstalled version and the repository's own `.bazelversion` are
  separate declarations for different purposes, currently both 8.6.0.
- LLVM major selection, feature implementation resolution, and test expectations
  live in separate files and express different levels of version specificity.
- Native lockfile registration in `MODULE.bazel`, public targets in
  `tools/BUILD.bazel`, installation lists in two features and the root post-create
  script, and individual feature assertions are maintained separately. The
  generated README checks catalog descriptions but does not validate all these
  registrations against each other.
- Python catalog access and documentation are coupled to the container installer.
  The Bazel macro separately validates the metadata it needs during analysis.
- System-wide `pre-commit` and user-level `pytest`/`basedpyright` use different uv
  installation policies. APT provides another set of Python CLIs.
- The documented pinned runner interface can execute arbitrary PATH versions.
  A container marker does not verify release alignment, and strict mode does not
  bypass that branch.

These observations describe the starting point for #190. Decisions about which
definitions to migrate, remove, or retain belong to the implementation work;
this snapshot does not assign new ownership or change delivery behavior.
