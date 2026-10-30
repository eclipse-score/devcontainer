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

# Local tool-management reference

The complete reference is implemented and validated locally on
`refactor/tool-management-reference`. All goal criteria passed on 2026-10-30;
nothing has been pushed or published. The
[completion audit](tooling-completion-audit.md) maps each criterion to evidence.

## Outcome and structure

Tool definitions own version decisions. Environment selections own direct
membership. Installers, installed-result verification and the generated inventory
consume those inputs. Existing backend formats and feature lifecycle boundaries
remain; standalone uv delivery is an additional consumer of the shared Python
definitions.

| Responsibility | Implemented owner |
| --- | --- |
| Native release definitions | `tools/lockfiles/*.lock.json`, consumed by multitool and container installation |
| Python package/version/entrypoint | Packaged literal `tools/score_tools/python_tools.bzl`, loaded by Bazel analysis and parsed by the shared Python reader |
| APT constraints and special setup metadata | `tools/providers.json`; exact request, prefix, distribution policy and compatibility expectation are distinct |
| Local feature/repository membership | `tools/environments.json`, including transient build APT dependencies and repository npm tools |
| External feature and image membership | Existing Dev Containers configs and locks, referenced from the inventory rather than copied |
| Installation | Container provider installer plus feature-specific setup, standalone `score-tool`, and existing Bazel macros |
| Availability and policy verification | `install.py verify-environment`, functional feature tests and process-boundary tests |
| Inventory and drift | `sync_readme.py`, shared catalog validation and pre-commit/CI checks |

Bazel's explicit native hubs and aliases are retained and checked against all
native definitions. Python targets derive from the dictionary. Digest refresh
derives uvx's repeated version field from uv, the basename-matching release owner.
Validation rejects inconsistent generated copies.
The proxy Dockerfile's base must agree with the default Dockerfile.

APT installation preserves the existing requests, including Debian epochs and
unversioned Git/Git LFS/gh selection. Their separate compatibility expectations
remain checks rather than fictional install pins. Normal APT recommendations
remain enabled, including Python build support, with QEMU retaining its existing
no-recommendations policy.

Python CLI installs use system entrypoints and isolated tool environments under
`/usr/local/share/uv/tools`. No installer guesses the development user from home
directory contents. Bazel completion uses the Dev Containers remote-user setting.
CodeQL pack members are defined once in the provider bundle and read by setup
and installed-pack verification. pip and venv retain their separate unpinned
APT policies, independent of the interpreter package-name constraint.
The removed yq bootstrap is intentionally absent: existing image Python reads the
shared data. Optional dive installation now reads its version and hashes from the
provider definitions, too.

## Delivery and compatibility decisions

Native and Python Bazel targets retain their existing names and working-directory
behavior. The old exported `tools/lockfiles/python_tools.bzl` label forwards to the
single literal owner. Bazel CLI execution still carries only shell and pinned uvx
at runtime; it adds no host Python prerequisite.

`score-dev-tools` packages the literal Python definitions and exposes `score-tool`.
The caller supplies compatible uv. Git-ref selection, not PyPI publication, binds
the package to a repository release:

```console
uvx --from 'git+https://github.com/eclipse-score/devcontainer.git@RELEASE' score-tool pre-commit run --all-files
```

`run-tool` retains container PATH precedence even with strict mode, host PATH
precedence without strict mode, and Bazel selection on a strict host invocation.
Those behaviors have contract tests. Documentation now states the practical
limit: PATH execution is not a version attestation. Downstream migration can use
direct Bazel targets or the new explicit uv command when catalog selection is
required; no downstream repository has been edited.

Exact native artifacts, Python direct pins, APT prefixes and OCI feature digests
provide different guarantees. Interpreter/transitive Python locking, APT
snapshots and reproducible image rebuilds remain follow-up work. Trust-store
refresh and deliberately distribution-following tools remain unpinned.

## Maintenance paths

- Add a definition, select its environment, and add provider-specific behavior
  only when needed. Explicit native Bazel registrations are checked; Python
  targets are derived. Availability checks and inventory use the selection.
- Update the owning version. Refresh native URLs/checksums and regenerate the
  overview. Release asset refresh now handles filenames containing versions and
  fails rather than silently leaving a stale digest. Existing Renovate managers
  follow the native definitions; other sources have explicit manual review owners.
- Remove an environment membership. Generic installation and verification follow
  it. Special Java/CodeQL/Bazel setup and functional checks query the same selection.
  Dependency validation rejects selecting packs without CodeQL or preinstalled
  Bazel without Bazelisk.

## Validation record

| Check | Current evidence |
| --- | --- |
| Repository hooks | `pre-commit run --all-files --show-diff-on-failure` passed, including license checks |
| Catalog/process tests | `python3 -m unittest discover -s tools/tests -p 'test_*.py'`: 20 passing tests; covers malformed definitions, selection drift, installed-version drift, argument/cwd/status boundaries and release-asset refresh |
| Existing shell/Bazel contracts | `bazel test //tools:python_tool_runner_test //tools:run_tool_test` passed |
| Real Bazel delivery | `bazel run //tools:pre-commit -- --version` reports 4.7.0; ShellCheck reports 0.10.0 |
| Git delivery outside checkout | `tools/tests/git_delivery_smoke.sh` passed at code commit `e848cc4`: real pre-commit 4.7.0, package data, cwd, argument boundaries and status 42 |
| Removing environment membership | A disposable container with OpenJDK removed from the selection runs the actual feature setup block without querying javac or changing its Java profile |
| Repository development image | amd64 and arm64 Dev Containers builds and derived smoke images passed: repository selection verified as node, including npm resolution, Docker, Dev Containers CLI and hook registration |
| Optional helper | `scripts/install_dive.sh` in disposable amd64 and arm64 development images verifies each artifact and reports dive 0.13.1 |
| No-host-Python Bazel execution | Minimal Ubuntu image passed with neither python nor python3 on PATH: Bazel runs pre-commit 4.7.0 using uv-managed CPython 3.15.2; a separate native ShellCheck invocation reports 0.10.0 |
| Published image amd64 | `score-tooling-reference:final-amd64` built successfully; all 38 embedded tool/feature source files match. Full development-user tests passed without tool/check overlays, including pycairo source compilation, Python/native tools, CodeQL plus packs, Bazel and temporary-package cleanup |
| Published image arm64 | `score-tooling-reference:final-arm64` built successfully; all 38 embedded tool/feature source files match. Full development-user tests passed without overlays, including pycairo source compilation and Bazel; CodeQL is intentionally unsupported on Linux arm64 |
| Final inventory / completion audit | 63 definitions validated and generated; all ten goal criteria have direct evidence in tooling-completion-audit.md |
| PR sequence | Seven dependency-ordered PRs derived from the validated reference, with concrete outcomes, working intermediate states and validation gates in tooling-pr-sequence.md |

Both final-source images embed the current installer, catalog, provider and
composition data, metadata bridge and feature installation scripts; SHA256 checks
confirm all 38 tool/feature source files match in each image. Functional tests
mount only the test project read-only. See the
[completion audit](tooling-completion-audit.md) for the requirement-by-requirement
record, exact local image identifiers and evidence locations.

The published-image build and functional test commands, from the repository root,
are below. ARM64 execution on an amd64 host requires working binfmt emulation;
the local verification uses emulation rather than native ARM hardware.

```bash
set -euo pipefail
for architecture in amd64 arm64; do
    npx --yes @devcontainers/cli build \
        --workspace-folder src/s-core-devcontainer \
        --image-name "score-tooling-reference:final-${architecture}" \
        --platform "linux/${architecture}"
    docker run --rm --platform "linux/${architecture}" --user vscode \
        --mount "type=bind,src=${PWD}/src/s-core-devcontainer/test-project,dst=/work/test-project,readonly" \
        --workdir /work/test-project "score-tooling-reference:final-${architecture}" \
        bash -lc 'exec bash test.sh'
done
```

Repository validation first builds its existing configuration:

```console
npx --yes @devcontainers/cli build --workspace-folder . --image-name score-tooling-repository:local --platform linux/amd64
npx --yes @devcontainers/cli build --workspace-folder . --image-name score-tooling-repository:arm64 --platform linux/arm64
```

The derived smoke image uses the following Dockerfile. For arm64, its FROM is
`score-tooling-repository:arm64`. Build it from the repository root with
`docker build --platform linux/amd64 -f SMOKE_DOCKERFILE .` (or linux/arm64).
The install runs as root; verification, command execution and hook registration
run as node, matching the repository's development user.

```dockerfile
FROM score-tooling-repository:local
USER root
COPY tools /usr/local/share/score-tools
RUN /usr/local/share/score-tools/internal/devcontainer/install.py environment repository
USER node
RUN /usr/local/share/score-tools/internal/devcontainer/install.py verify-environment repository \
    && docker --version \
    && devcontainer --version \
    && mkdir /tmp/score-hook-smoke \
    && cd /tmp/score-hook-smoke \
    && git init \
    && pre-commit install
```

Build logs for this local run are under `/tmp/score-image-final-amd64.log`,
`/tmp/score-image-final-arm64.log`, `/tmp/score-repository-final-amd64.log`,
`/tmp/score-repository-final-arm64.log`, and
`/tmp/score-no-host-python.log`. These are local evidence, not publication outputs.
