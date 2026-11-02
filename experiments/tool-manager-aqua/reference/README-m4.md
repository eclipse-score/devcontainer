<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Aqua maintenance milestone 4

> Historical M4 evidence. Its prepared-runtime handoff, `--stage-devcontainer`,
> and `check_devcontainer.py` were retired in M5. Use the current [README](README.md)
> and [M5 ledger](README-m5.md) for maintained commands and ownership.

## Result

The current published selection contains native starpls 0.1.22 and Python
codespell 2.4.1. `//tools:starpls` retains its existing native label and the
`bazel-feature` composition; `//tools:codespell` is generated from the existing
Python catalog. Codespell is also in the published Python group, the
`s-core-local` Python composition, and the ordinary `codespell` extra in the
standard facade. The `repository` selection is unchanged.

The fresh immutable local facade/release is 0.3.2. The M3 0.3.1 release is
rejected against current owner snapshots. The previously built M3 DevContainer
image remains historical and was not rebuilt for these owners.

## Maintainer operations and adapter work

| Work | Current operation | Next similar tool or update |
| --- | --- | --- |
| Native selection | `reference/aqua.yaml` pins starpls once and selects it only for `published`; its version remains 0.1.22. | For a standard-registry package, add the owner entry and tags, then refresh generated checksums. A later starpls version uses the same normal pin and refresh path. |
| Python selection | `reference/pyproject.toml` owns codespell 2.4.1 in `published`; `tools/environments.json` adds its command to `s-core-local`, leaving `repository` untouched. | Add the direct requirement to the intended Python group and add feature membership where needed. The version is not repeated in consumer input. |
| Python public identity | `tools/score_tools/python_tools.bzl` adds package, entrypoint, and description fields for codespell without an authored version; the existing generator writes 2.4.1 from the Python owner. | Add identity fields for each new Python command. The existing Python target comprehension creates its Bazel label without a `BUILD.bazel` edit. |
| Generated compatibility output | The existing producer/exporter updates aqua checksums, root native locks, Python versions, facade extras, and tool documentation. | Run the same checksum refresh and current-owner generation after an owner change; generated outputs are not another version source. |
| Local registry policy | The pinned standard registry `v4.579.0` has no `withered-magic/starpls` package: the exact `aqua generate withered-magic/starpls@v0.1.22` lookup returned `unknown package`. `starpls-registry.yaml` supplies a declarative raw GitHub release recipe, while `aqua-policy.yaml` allows the `score-local/withered-magic/starpls` package identity and pinned standard registry without another version pin. | This is a starpls-specific route for the missing standard entry. A later starpls version only changes the aqua owner pin and generated checksums. Another package missing from the standard registry would need its own reviewed recipe and, if its asset layout differs, adapter support. The [aqua registry](https://aquaproj.github.io/docs/reference/registry-config/) and [policy](https://aquaproj.github.io/docs/guides/policy-as-code/) are the native mechanisms used here. |
| Release snapshot | `prepare.py` copies the local registry and policy beside `aqua.yaml` and applies the snapshot-relative policy when aqua prepares the immutable output. | This closes the producer's local-registry snapshot gap for this owner. A newly introduced local registry file must also be included in the snapshot inputs. |
| Bazel artifact adapter | `export_native.py` maps starpls raw asset names and Linux architecture spellings to the existing root lockfile format and reuses aqua-generated checksums. The resulting root lock preserves the old URLs, SHA-256 values, platforms, version, and label identity. | This mapping is a one-time adapter for the existing starpls layout. A release update only regenerates hashes and root metadata; a different raw/archive layout needs an explicit bounded mapping. |
| Release owner drift | `check.py` compares native config, local registry, policy, and Python group snapshots before accepting a prepared release. | Keep each new owner input in this guard so changes make old releases stale. |

No generic catalog framework was added. Aqua owns native versions, registry
recipes, and checksums; Python dependency groups own Python versions. The root
lockfiles, facade extras, generated Python version, and prepared manifest are
compatibility outputs derived from those owners.

## Preparation and observed behavior

Using the existing pinned aqua 2.65.2 and uv 0.11.2 producer binaries, the
fresh release was prepared from the existing Linux amd64 Ubuntu producer image:

```sh
export AQUA_BINARY=/tmp/score-aqua-eval/bootstrap/aqua
export AQUA_ROOT_DIR=/tmp/score-aqua-eval/root
export UV_BINARY=/tmp/score-aqua-eval/bin/uv
export UV_CACHE_DIR=/tmp/score-m3-aqua/uv-cache
export SCORE_PREPARED_RUNTIME_IMAGE=score-aqua-m3-base:local-amd64
python3 experiments/tool-manager-aqua/reference/prepare.py \
  /tmp/score-m4-aqua/replay-release --version 0.3.2 --sync-repository \
  --target-platform linux/amd64 \
  --stage-devcontainer /tmp/score-m4-aqua/replay-prepared-tools
```

`prepare.py` supplies the worktree-local aqua policy to its aqua subprocesses.
For a direct native copy, use the same scoped policy explicitly:

```sh
export AQUA_POLICY_CONFIG="$PWD/experiments/tool-manager-aqua/reference/aqua-policy.yaml"
"$AQUA_BINARY" -c experiments/tool-manager-aqua/reference/aqua.yaml \
  cp --tags published -o /tmp/score-m4-aqua/replay-native/bin
```

The executed release and evidence are under `/tmp/score-m4-aqua/`. The
generated selection contains starpls 0.1.22 and codespell 2.4.1 under
`published`; neither appears in `repository`. The ordinary wheel's exact
metadata includes:

```text
Requires-Dist: codespell==2.4.1; extra == "published"
Requires-Dist: codespell==2.4.1; extra == "codespell"
```

An ordinary uv project added only
`score-aqua-reference[codespell] @ file:///.../score_aqua_reference-0.3.2-py3-none-any.whl`,
then locked, synced, and ran codespell. `uvx --with` the same facade extra also
ran it. Both reported `teh ==> the`; neither consumer authored a second
codespell version.

The shared `onboarding-runtime-check.py` passed against (1) native aqua starpls
plus prepared codespell and (2) both tools from the staged prepared runtime.
Both checks ran inside the producer container with `--network none`. They
verified the real starpls `initialize`/`shutdown` LSP exchange, tool versions,
clean text, and the codespell typo diagnostic. They do not claim project
indexing or substitute for a full production image build. In both runs,
starpls also attempted background `bazel info`; the pinned Bazel 8.6.0 could
not resolve the Bazel Central Registry host while networking was disabled.
That discovery failure did not prevent the protocol exchange from completing.

The actual root Bazel targets passed their intended behaviors:

- `//tools:starpls -- version` reported `v0.1.22`.
- `//tools:codespell -- /tmp/score-m4-aqua/bazel-typo.txt` reported
  `teh ==> the` and returned the expected diagnostic exit 65.

The generated production handoff passed `check_devcontainer.py` for
`linux/amd64`. It verified 13 commands and both feature selections; codespell
took the prepared Python skip path in `s-core-local`, and starpls took the
prepared native skip path in `bazel-feature`. Focused regression coverage also
checks that remaining APT and unmigrated commands stay selected and are still
sent through their existing installers.

Current-owner `sync_repository.py --check`, tool README drift, all 24 tool
catalog tests, Ruff, yamlfmt, Python compilation, and Buildifier checks passed.
The old M3 0.3.1 release was rejected as stale at `aqua.yaml` before acceptance.
The repository selection in 0.3.2 exactly matches the M3 release selection.

## Limits and peer source review

Network was available during aqua preparation, Bazel, and uv consumer
operations; the two shared behavior probes were explicitly network isolated.
The cached Bazelisk/Bazel 8.6.0 provider was reused for the LSP probe. Native
checksums describe Linux amd64/arm64 and macOS arm64, but only Linux amd64 ran.
No full LLVM/APT/CodeQL DevContainer build, ARM/macOS execution, release
publication, or update automation was attempted. The M3 image has not been
validated against the new owners.

Cross-reading current peer owner sources found two useful boundaries: mise
uses its `github:withered-magic/starpls` and `pypi:codespell` backends in the
published-only config. Nix selects `pkgs.starpls` 0.1.22 and `pkgs.codespell`
2.4.3 from its locked nixpkgs input and lists both in `published`, not
`repository`; the Python package alias is absent in that locked input. Thus
Codespell follows its manager's owner (2.4.1 in aqua/mise, 2.4.3 in Nix), while
the same selection outcome uses different native backends. Aqua's additional
local recipe and raw-asset adapter follow from the missing package in its
pinned standard registry; that burden should not be generalized to managers
whose native package source already resolves starpls.
