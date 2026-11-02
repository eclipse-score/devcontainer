<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Nix M7: Linux ARM64 execution

Status: Nix candidate M7 runtime checks completed on 2026-11-02. This is
candidate evidence, not a manager selection or adoption claim. No commits,
pushes, publication, or full feature-image build were performed.

## Prepared output and owner check

The maintained `tools/internal/nix/prepare.py` API prepared a fresh
`aarch64-linux` release at `/tmp/score-m7-nix/release-arm64` with explicit
identity `score-devcontainer-nix-candidate` version `0.0.0+m7.nix`. It contains
the current `published` profile and its Python packages. The Nix producer was
x86_64; the release manifest records that producer-side execution probes were
deferred rather than treating target executables as observed.

Exact preparation command:

```sh
python3 tools/internal/nix/prepare.py /tmp/score-m7-nix/release-arm64 \
  --release-version '0.0.0+m7.nix' \
  --package-name score-devcontainer-nix-candidate \
  --system aarch64-linux \
  --defer-native-observation \
  --allow-aarch64-emulation
```

A dry run found 228 `cache.nixos.org` substitutes (329.2 MiB download, 1.1
GiB unpacked) and four derivations to realize. The build fetched those package
closures and used QEMU-enabled Nix execution for the small number of missing
release/profile derivations; it did not compile the large tool runtimes from
source. The copied release closure occupies about 1.3 GiB. Disk remained above
the 4 GiB floor throughout; final free space was 7.1 GiB.

These validations passed:

```sh
python3 tools/internal/nix/package.py check /tmp/score-m7-nix/release-arm64
python3 tools/internal/nix/sync.py --check \
  --release /tmp/score-m7-nix/release-arm64 --system aarch64-linux
python3 /tmp/score-m7-nix/verify-release-closure.py \
  /tmp/score-m7-nix/release-arm64
```

`sync.py` reported no stale outputs. The closure verifier resolved both current
owner profile paths and matched all 181 recursive store paths against the
prepared output. All 15 versions and published/repository membership match M6
exactly. No M5 or M6 release was modified.

## ARM64 runtime checks

The task container used the existing `score-tooling-reference:final-arm64`
image, ID
`sha256:b36448960057f54745f841561338487c5e9e2128526113c24b4861a7cf0f065a`,
with Docker's QEMU/binfmt ARM64 execution. It ran as `1000:1000`, with network
disabled, a read-only root filesystem, a read-only Nix store mount, and only
small read-only fixtures mounted. The selected published bundle was first on
`PATH`; every successful version check asserted that the command came from that
fresh bundle and resolved inside `/nix/store`. The successful checks invoked
no Nix manager or Bazel. The base image's older tool installations were not
used as candidate output.

Exact container command:

```sh
docker run --rm \
  --name score-m7-nix-arm64-runtime \
  --label score-m7-platform.candidate=nix \
  --platform linux/arm64 \
  --network none \
  --user 1000:1000 \
  --read-only \
  --tmpfs /tmp:rw,nosuid,size=512m \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --mount type=bind,source=/tmp/score-m7-nix/release-arm64/native/nix/store,target=/nix/store,readonly \
  --mount type=bind,source=/tmp/score-m7-nix/stage,target=/m7,readonly \
  --entrypoint /bin/bash \
  b36448960057f54745f841561338487c5e9e2128526113c24b4861a7cf0f065a \
  /m7/run-arm64-checks.sh
```

The runtime reported UID 1000 and `uname -m` = `aarch64`. The selected Nix
Python runtime was 3.14. The base image also contains Python 3.12.3, but the
pytest fixture asserted that the selected Python CLI ran under Python 3.14 on
`aarch64`.

| Selected published command | Owner version | Result |
| --- | ---: | --- |
| actionlint | 1.7.12 | Passed, ARM64 binary |
| apm | 0.35.0 | Passed |
| basedpyright | 1.39.8 | Passed; valid source reported 0 errors |
| bazelisk | 1.29.0 | **Unverified.** See limitation below. |
| buildifier | 10.2.0 | Passed |
| codespell | 2.4.3 | Passed on clean fixture |
| opencode | 2.2.3 | Passed |
| pre-commit | 4.7.0 | Passed; `validate-config` succeeded offline |
| pytest | 9.1.1 | Passed; one test confirmed Python 3.14 and `aarch64` |
| ruff | 0.17.2 | Passed; expected negative diagnostic also verified |
| shellcheck | 0.11.0 | Passed on clean Bash fixture |
| starpls | 0.1.22 | Passed |
| uv | 0.13.5 | Passed; reported `aarch64-unknown-linux-gnu` |
| uvx | 0.13.5 | Passed; reported `aarch64-unknown-linux-gnu` |
| yamlfmt | 0.21.0 | Passed on clean YAML fixture |

Ruff's functional negative case ran the selected binary on a file with an
unused `os` import. It exited 1 and emitted:

```text
m7/fixtures/ruff_fail.py:1:8: F401 [*] `os` imported but unused
Found 1 error.
[*] 1 fixable with `--fix`.
```

`uvx` also ran offline with the M6-built local
`score-devcontainer-nix-candidate[ruff]` wheel and an ARM64 Ruff wheel staged
before the container started. It printed `ruff 0.17.2`; no package index or
network was available at runtime. The facade wheel SHA-256 is
`eb5f63657cf15936ede2dda390e01389b79b3dbefe94a9ddcb14382b4445bbd0`; the
ARM64 Ruff wheel SHA-256 is
`b7d0906677d89bbf3cf73cde64b5bbe2ab35df3ae43e49ee2627301e91265bac`.

Both direct and strict SCORE runner paths worked from the fresh prefix:

```sh
bundle=/nix/store/vaaacix8fd8dvka8hpr0c548j37n9ybd-score-tools-published
PATH="${bundle}/bin:/usr/bin:/bin" RUN_TOOL_CONTAINER_MODE=container \
  /bin/bash /m7/tools/run-tool --strict ruff --version
RUN_TOOL_CONTAINER_MODE=host SCORE_NIX_PROFILE_BIN="${bundle}/bin" \
  PATH=/usr/bin:/bin /bin/bash /m7/tools/run-tool --strict uv --version
```

A strict request for `not-selected` with `PATH=/m7/empty` exited 127 and
reported that no container command or Bazel executable was available. This
confirmed the prepared-call failure path without invoking Bazel.

### Bazelisk limitation

The shared M7 contract excludes Bazel invocations. A bounded attempt to query
Bazelisk itself with `bazelisk --bazelisk-version` produced no output after 22
seconds in the network-disabled container and was stopped with
`docker kill --signal=KILL score-m7-nix-arm64-runtime`. It is not counted as a
pass. This is an execution-policy limitation, not an observed ARM64 package
failure. The exact attempt is recorded in
[`bazelisk-attempt.md`](/tmp/score-m7-nix/bazelisk-attempt.md).

## macOS ARM review (not executed)

Nix evaluation for `aarch64-darwin` retained the same 15 selected versions and
both profile lists. Fourteen Nixpkgs package records list `aarch64-darwin` in
`meta.platforms`. OpenCode is a custom derivation with no generic platform list;
the flake explicitly selects `opencode-darwin-arm64.zip`, uses `unzip`, and
has a matching `aarch64-darwin` hash. No macOS build or execution was run, so
this is configuration review only.

## M7 source repair and regression checks

The maintained release API previously tried to execute target binaries inside
its x86_64 Nix producer. `prepare.py` now detects the producer architecture,
rejects cross-system probes by default, and supports explicit
`--defer-native-observation`; a deferred release records target and producer
systems in `release.json`. The bounded `--allow-aarch64-emulation` option adds
Nix's `extra-platforms` setting only for an `aarch64-linux` target on an
`x86_64-linux` producer.

The amd64 default still runs producer probes. Seven focused unit tests cover
architecture mapping, fail-closed cross-target behavior, explicit deferral,
and the emulation option. They passed with:

```sh
python3 -m unittest discover -s tools/internal/nix -p 'test_*.py'
```

Ruff lint, formatting for the new test file, Python compilation, and
`git diff --check` passed. After the source change,
`sync.py --check --release /tmp/score-m6-nix/release-amd64 --system
x86_64-linux` still passed with no stale outputs. The unchanged M6 amd64 release
was not regenerated or modified.

## Maintenance ledger

| Boundary | One-time M7 work | Recurring owner |
| --- | --- | --- |
| Cross-system release preparation | Added explicit probe deferral and bounded aarch64-on-x86 QEMU build opt-in with regression tests. | `tools/internal/nix/prepare.py` selects target, records deferred observations, and produces the Nix closure. |
| Shared versions and selection | No tool pins or profile membership changed. | `tools/nix/flake.nix` and `flake.lock`; refresh compatibility exports through `tools/internal/nix/sync.py`. |
| Linux ARM64 command surface | Prepared and executed the current `published` profile from a read-only fresh store. | Nix substitutes, closure transfer, and activation remain Nix release-operation responsibilities. |
| Python dependency interface | Reused the existing M6 local facade wheel; no second pins were added. | `tools/internal/nix/package.py` derives exact extras from the selected catalog and release manifest. |
| Cross-platform assets | Verified ARM64 OpenCode hash and Linux Nix package substitution. | Maintain per-platform upstream assets/hashes and check package support in Nixpkgs. |
| macOS ARM | Read-only metadata review; execution remains unverified. | Validate Darwin package/platform metadata and run on macOS before claiming support. |

## Evidence files and limits

The compact machine-readable record is
[`result.json`](/tmp/score-m7-nix/result.json). Raw preparation, closure,
unit-test, runtime, and failed-attempt logs remain in `/tmp/score-m7-nix/`.
This run used QEMU/binfmt, not native ARM hardware. No full feature image was
built. No manager was selected, and no adoption, hosted workflow, or
publication decision is implied.
