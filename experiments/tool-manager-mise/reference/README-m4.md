<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Mise M4: native starpls and Python codespell

This milestone adds two real tools to the existing published delivery paths.
`starpls` keeps its 0.1.22 version and existing `//tools:starpls` identity;
`codespell` is pinned once at 2.4.1 and is available from the published Python
facade and the `s-core-local` composition. The smaller repository selection is
unchanged. No changes were published or committed.

The [licensed maintenance ledger](evidence/m4/maintenance.json) records owner
choices, adapter work, generated outputs, execution observations and limits.

## Policy and recurring maintainer work

| Work | Current owner and action | Work for a similar next tool |
| --- | --- | --- |
| Select starpls | `mise.published.toml` selects `github:withered-magic/starpls` at 0.1.22. It stays in the existing Bazel feature selection. | Choose the native source, version and published profile. A package with a new backend or executable identity needs an adapter entry as described below. |
| Select codespell | `mise.published.toml` selects `pypi:codespell` at 2.4.1; `tools/environments.json` adds it to `s-core-local.python`. | Choose the published version and the feature composition that needs the command. The repository arrays do not change for this addition. |
| Publish a Python command | The data-only root Python catalog records codespell's distribution, console entrypoint and description. Release generation takes its version from the mise owner. | Add public package/entrypoint/description metadata. Version remains generated from the native owner; no second codespell version is maintained. |
| Expose the Bazel label | Existing `[python_tool(name) for name in PYTHON_TOOLS]` generates `//tools:codespell`. Existing `//tools:starpls` stays registered. | Add Python identity metadata; no per-command BUILD registration is needed. |

`tools/environments.json` differs only by adding codespell to the `s-core-local`
Python selection. Its repository native/Python/npm selections, `s-core-local`
APT/native selections and `mise.repository.toml` remain unchanged.

## Adapter and producer work

| Adapter change | Purpose and maintenance classification |
| --- | --- |
| Add the GitHub starpls backend to the exporter identity map and to the producer's backend-to-executable map. Add `pypi:codespell` to the producer executable map. | The release exporter needs a root tool identity, and runtime export needs the actual command name. Repeat these mappings when a new backend or executable identity is introduced. |
| Generate a separate published-profile native lock from its non-PyPI entries. | The published config mixes a native release with PyPI commands. Locking only native entries retains the direct Python version pins and avoids making Python dependency graphs a new mise-owned runtime decision. This is a one-time profile-lock integration gap; future published native entries are discovered by the producer. |
| Reuse the existing archive exporter for starpls. | The GitHub lock resolves `.tar.gz` release assets whose top-level executable is `starpls`. The existing root lock format represents this as `kind: archive`, `file: starpls`, `type: tar.gz`; no wrapper or hand-authored digest was needed. Root compatibility metadata keeps the existing version and three supported platforms: Linux x86_64, Linux arm64 and macOS arm64. |
| Add the new Python identity to the shared root catalog and prepared-runtime regression input. | The identity enables the existing uvx launcher and automatic Bazel target. The regression reads generated `prepared-selection.json`, verifies codespell and starpls skip the prepared paths, and keeps the unprepared starpls catalog download as fallback. APT and unmigrated native paths remain in their normal installer calls. |
| Allow checksum-verified reuse of a pinned mise binary and opt-in root-output refresh during production preparation. | `SCORE_MISE_BOOTSTRAP_BINARY` avoids downloading the already available pinned CLI. `SCORE_MISE_REFRESH_ROOT=1` writes generated root compatibility outputs before staging the runtime, so a current release can be prepared in one producer run. These are one-time producer-operation gaps, not per-tool steps. |

The standard Aqua registry lookup for `aqua:withered-magic/starpls` returned
`registry not available: no aqua-registry found for withered-magic/starpls`.
The native `github:withered-magic/starpls` backend locked and installed the
authentic project release at 0.1.22. The exact lookup evidence is in
[`native-lookups.txt`](evidence/m4/native-lookups.txt). This is a registry
boundary, not a reason to substitute another language server or invent a
Python package.

## Generated outputs

The producer refreshed the published native lock and generated the existing
root consumers from the current owners:

- `mise.published.lock` records starpls checksums for the configured Linux
  x64/arm64 and macOS arm64 platforms.
- `tools/lockfiles/starpls.lock.json` has the existing 0.1.22 version and
  generated archive metadata. `tools/score_tools/python_tools.bzl` contains the
  codespell identity at the owner-derived version, and the existing Python
  target comprehension exposes its Bazel label.
- `tools/prepared-selection.json` selects starpls for `bazel-feature` and
  codespell for `s-core-local`. Its owner hash matches the prepared-tools
  manifest. Codespell is absent from the repository runtime output.
- `reference/generated.pyproject.toml` and the fresh 0.6.1 release contain the
  standard `codespell` extra. The built wheel's exact metadata is recorded in
  [`uv-facade.txt`](evidence/m4/uv-facade.txt); existing extras remain present.
- `tools/README.md` was regenerated from the root catalog. Its drift check
  passes.

The producer command used the existing pinned binary and M3 runtime store:

```sh
SCORE_MISE_BOOTSTRAP_BINARY=/tmp/score-m3-mise/bootstrap/mise \
SCORE_MISE_PRODUCER_IMAGE=score-mise-m3:local-amd64 \
SCORE_MISE_REFRESH_ROOT=1 \
  experiments/tool-manager-mise/reference/prepare-production.sh \
  /tmp/score-m4-mise/prepared-context-m4 linux/amd64 0.6.1
```

The M3 image supplied the unchanged tool roots and matching Ubuntu system
Python to the producer. It was not built, installed as the M4 consumer image,
or used as current-owner image proof. On a clean machine the helper can use its
default `buildpack-deps:noble-curl` producer image instead.

## Observed execution

| Path | Observation |
| --- | --- |
| Fresh native release and prepared context | Both outputs passed the shared checker at uid 1000 with `--network none`, using absolute starpls and codespell paths from their own generated artifacts. The checker observed versions 0.1.22 and 2.4.1, completed starpls initialize/shutdown, and reported the actual codespell `teh ==> the` diagnostic. See [`native-runtime-check.json`](evidence/m4/native-runtime-check.json) and [`prepared-runtime-check.json`](evidence/m4/prepared-runtime-check.json). |
| Real root Bazel labels | `//tools:starpls` ran `starpls version` at 0.1.22. The generated `//tools:codespell` label ran at 2.4.1 and reported the typo fixture. Bazel had normal network access. |
| Ordinary Python facade | The built wheel declares `Requires-Dist: codespell==2.4.1; extra == "codespell"`. A normal uv consumer completed lock, sync and run; uvx used `--with "score-mise-reference[codespell] @ <wheel>"`. Neither consumer supplied a second codespell version. Network access was available. |
| Handoff and drift | Fresh release/root and prepared-context checks passed. The previous M3 release was rejected with `Stale release input: mise.published.toml`. Focused `//tools:prepared_runtime_test` and `//tools:python_tool_runner_test`, root README drift, Ruff, ShellCheck, Buildifier, shell syntax and `git diff --check` passed. |

Detailed outcomes and the commands' observed network conditions are in
[`root-bazel.txt`](evidence/m4/root-bazel.txt),
[`handoff-and-release.txt`](evidence/m4/handoff-and-release.txt) and
[`source-checks.txt`](evidence/m4/source-checks.txt).

## Peer source cross-read

Aqua’s current source defines a local raw GitHub release recipe for Starpls,
bundles its registry and policy into each prepared release, and translates the
Linux arm64 asset name to `aarch64` when exporting the existing root lock. Its
pinned standard registry had no Starpls package, so those are concrete
Aqua-specific additions. Nix instead selects `pkgs.starpls` and `pkgs.codespell`
from its locked flake. Its Starpls version matches the root lock, so the
exporter retains the existing asset checksums.

The candidates also follow their own Codespell package sources: Aqua and mise
use PyPI 2.4.1; Nix’s locked package attribute provides 2.4.3. The useful
transfer is to compare the owner-to-consumer steps and keep generated
compatibility output tied to each owner. Registry recipes, package attributes,
and asset mappings are specific adapter work, not recurring steps for every
manager.

## Limits

The M3 image contains a legacy `/usr/local/bin/starpls`. The runtime checker
was given absolute executable paths from the fresh M4 native and prepared
outputs, so that legacy path did not supply the tested command. The checker ran
offline: the LSP protocol exchange succeeded, while starpls's asynchronous
Bazel context setup logged a BCR registry cache miss. This is not a project
indexing or analysis result.

No M4 full DevContainer image was built. Only Linux amd64 preparation and
execution are covered; other-platform lock metadata is not execution evidence.
Publication, update automation, remaining catalog migration and downstream
compatibility are outside this milestone.
