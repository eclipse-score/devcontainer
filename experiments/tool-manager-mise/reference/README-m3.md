<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Mise M3: prepared runtime in the production DevContainer

Completed locally 2026-11-01 against the real `src/s-core-devcontainer`
configuration. The full Linux amd64 image was built through the standard build
entrypoint; the existing production test suite and the coordinator's shared
44-command offline acceptance passed on the final stable-prefix image. The
earlier task-local offline smoke is retained only as historical evidence for
the previous `/tmp`-prefix image. Nothing was published or committed.

## Integration and ownership

The published producer now stages a complete runtime closure plus generated
handoff metadata for the actual feature selections. `tools/prepared-selection.json`
comes from current native/Python mise owners and the existing environment
composition. It adds no independently maintained version list. The handoff
records the owner hash, versions, runtime roots, executable paths, and digests.

The production Dockerfile imports that closure through a BuildKit named
context. Both local feature installers pass the handoff to
`tools/internal/devcontainer/install.py`. Before skipping a selected native or
Python catalog installation, the installer validates owner metadata, exact
manifest membership, catalog versions, runtime/executable presence, PATH
identity, and executable SHA256. Invalid or missing metadata stops feature
installation. Per-feature build output records the verified selections being
skipped. APT requirements still install; unmigrated native and Python tools,
setup providers, the full common-utils and LLVM feature chain, CodeQL and packs,
APM/opencode, and Bazel's explicit 8.6.0 provider lifecycle remain in place.

The image receives 11 prepared commands across the two features:

- `s-core-local`: actionlint, basedpyright, pre-commit, pytest, Ruff, ShellCheck,
  uv/uvx, and yamlfmt.
- `bazel-feature`: Bazelisk and Buildifier. `starpls` remains on its existing
  install path.

`uv`/`uvx` keep their ordinary package-consumption interfaces. Existing M2
evidence continues to cover real published package resolution and the
simple-tool-only Bazel packaging boundary; those broad probes were not rerun.
The existing `run-tool` implementation is unchanged. Container normal and
strict modes resolve installed PATH commands directly, while strict host mode
continues to use its pinned Bazel target.

## Reproduce the producer and build

The pinned mise binary and producer state are isolated. Preparation runs inside
a task-owned Linux amd64 container and installs the complete runtime at
`/opt/score-tools/prepared-runtime/data`; only its fresh release and Docker
context are mounted to task-local host paths. The consumer image has no producer
cache or runtime bind mount.

```sh
experiments/tool-manager-mise/reference/prepare-production.sh \
  /tmp/score-m3-mise/prepared-context linux/amd64 0.5.0
PATH="/tmp/score-m3-common/devcontainer/node_modules/.bin:$PATH" \
BUILDX_BUILDER=default \
SCORE_MISE_PREPARED_CONTEXT=/tmp/score-m3-mise/prepared-context \
  scripts/build.sh --amd64 mise-m3-final
```

`prepare-production.sh` defaults to `buildpack-deps:noble-curl`, matching the
target's Ubuntu 24.04 and `/usr/bin/python3`. It installs Python/venv only inside
the isolated producer when needed and disables managed-interpreter fallback, so
exported venvs do not depend on disposable producer state. An independent fresh
default run verified all three interpreter links; see
[`mise.default-producer.json`](evidence/m3/mise.default-producer.json).
`SCORE_MISE_PRODUCER_IMAGE` can select another compatible Ubuntu 24.04 image;
the main image-build preparation used the existing full S-CORE candidate image.
The helper refuses existing release/context paths. The generated handoff carries
`target_platform`, and the standard
build entrypoint rejects missing, stale, or cross-platform contexts before
starting Docker. This producer currently supports linux/amd64; `--arm64` is
rejected until matching runtime artifacts are prepared.

## Acceptance evidence

[`evidence/m3/`](evidence/m3/) retains the compact build identity and selected
feature output, the actual image's prepared manifest, the complete existing
production test output, focused context/platform gate checks, the focused Bazel
regression, and the verified default producer run. The shared offline evidence
is in [`production-evidence/mise`](../../tool-manager-comparison/production-evidence/mise.command.json).
Companion `.license` files follow the repository evidence convention.

| Check | Result |
| --- | --- |
| Full modified DevContainer build | Passed through `scripts/build.sh`, `linux/amd64`, image `ghcr.io/eclipse-score/devcontainer:mise-m3-final-amd64` (also tagged locally as `score-mise-m3:local-amd64`); complete common-utils, LLVM, `s-core-local`, and Bazel feature chain ran. Default and proxy Dockerfiles stage the same runtime. |
| Existing `test-project/test.sh` | Passed as `vscode` in a login shell, including CA/Java trust, LLVM, APT, native/Python versions, CodeQL/packs, Bazel 8.6.0, and compilation database checks. |
| Shared final offline acceptance | Passed: 44 commands, uid 1000, `--network none`, with only the acceptance script/expected-data mounts. This covers versions, direct and both `run-tool` modes, formatter/diagnostic fixtures, pre-commit, pytest, basedpyright, and Bazel 8.6.0. |
| Earlier offline smoke | Passed on the earlier `/tmp`-prefix image. Preserved as `evidence/m3/offline-check-pre-stable-prefix.log`; it does not validate the final image. |
| Focused handoff regression | Bazel `//tools:prepared_runtime_test` passed: prepared native/Python selections bypass downloaders, `starpls` remains selected for catalog installation, APT still runs, and missing/stale/corrupt handoffs fail. |
| Standard build gates | Missing/stale context and amd64-to-arm64 requests fail before Docker; producer rejects unsupported arm64 preparation. |
| Source consistency | Producer root drift, README sync, Ruff check/format, ShellCheck, Buildifier, default/proxy handoff parity, and `git diff --check` passed. |

The final production test suite ran online for its existing source/package
downloads. The earlier offline smoke covers runtime checks only and does not
claim that the complete production suite works offline.

## Peer review lesson

Aqua and Nix both validate platform and freshness before BuildKit starts and
keep the ordinary and proxy Dockerfiles on the same handoff. Mise now does the
same in `scripts/build.sh`; each candidate retains its own generated manifest
because the owner records differ. Nix also confirmed the base image has no
Python, so the runtime installer stays in the local feature lifecycle after
common-utils provides it. Aqua's Bazelisk path finding is covered here by the
prepared `/usr/local/bin/bazelisk` link and the unchanged pinned Bazel feature.

## Remaining adoption work

Only Linux amd64 was built. The native/Python subset is bounded to the current
feature compositions; this does not migrate the remaining native catalog or
replace APT, setup providers, external features, CodeQL, or the Bazel provider.
Release/update automation, other architectures, external CI, publication, and
downstream compatibility are not covered.
