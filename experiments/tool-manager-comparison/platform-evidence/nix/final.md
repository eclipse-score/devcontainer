<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Nix M7 handoff

**Status:** prepared and executed the Nix `published` selection on Linux ARM64
under QEMU/binfmt. Fourteen of fifteen selected commands completed offline
version/behavior checks. Bazelisk remains unverified because its attempted
self-version query did not return without network and M7 excludes Bazel
invocation. No manager was selected; no commit, push, image build, or
publication occurred.

The six M6 root gates are recorded as passed in the root-owned comparison
milestone. This worker made no changes to the root comparison checkout.

## Prepared output

- Release: `/tmp/score-m7-nix/release-arm64`
- Identity: `score-devcontainer-nix-candidate==0.0.0+m7.nix`
- System: `aarch64-linux`, platform `linux/arm64`
- Published profile: `/nix/store/vaaacix8fd8dvka8hpr0c548j37n9ybd-score-tools-published`
- Closure: 181 store paths; all paths and both profile bundles matched the current flake owner.
- `package.py check` passed; `sync.py --check --release ... --system aarch64-linux` passed with no stale outputs.
- Tool versions and profile membership are unchanged from M6. Nix substituted 228 paths (329.2 MiB download, 1.1 GiB unpacked) and realized four derivations; no large tool runtime was compiled.

Exact preparation and validation commands:

```sh
python3 tools/internal/nix/prepare.py /tmp/score-m7-nix/release-arm64 \
  --release-version '0.0.0+m7.nix' \
  --package-name score-devcontainer-nix-candidate \
  --system aarch64-linux \
  --defer-native-observation \
  --allow-aarch64-emulation
python3 tools/internal/nix/package.py check /tmp/score-m7-nix/release-arm64
python3 tools/internal/nix/sync.py --check \
  --release /tmp/score-m7-nix/release-arm64 --system aarch64-linux
python3 /tmp/score-m7-nix/verify-release-closure.py \
  /tmp/score-m7-nix/release-arm64
```

The runtime used image ID
`sha256:b36448960057f54745f841561338487c5e9e2128526113c24b4861a7cf0f065a`,
`--platform linux/arm64`, UID `1000:1000`, `--network none`, read-only root,
store and fixtures. It reported `uname -m=aarch64`; selected `uv` reported
`aarch64-unknown-linux-gnu`. Every command resolved to the fresh published
bundle/store, not the substrate's old tools.

The exact container launch ran
`/tmp/score-m7-nix/stage/run-arm64-checks.sh` (SHA-256
`2980efc15e9824c4e7b7cd9fda9cc4b258e92de5c18884350c8263780da6c1f2`). It
passed all 14 completed command version checks, offline pre-commit config
validation, one pytest test asserting Nix Python 3.14 on aarch64, a
basedpyright check with zero diagnostics, and actionlint, buildifier,
codespell, ShellCheck, and yamlfmt fixtures. Ruff emitted its expected F401
unused-import diagnostic and exited 1. Direct and strict `run-tool` invocations
passed; strict missing-tool handling returned 127 without Bazel in PATH.
`uvx --offline` consumed the M6 facade wheel's `[ruff]` extra plus a staged
ARM64 Ruff wheel and printed `ruff 0.17.2`.

Bazelisk `1.29.0` was not counted. The attempted
`bazelisk --bazelisk-version` command remained active with no output for 22
seconds in the offline task container and was stopped. Details and partial log
are in `/tmp/score-m7-nix/bazelisk-attempt.md` and
`/tmp/score-m7-nix/arm64-bazelisk-attempt.log`.

## Source repair and regression evidence

`prepare.py` now detects its Nix producer system, fails closed on cross-system
execution probes by default, records explicit deferred observations, and has a
narrow opt-in for aarch64-on-x86 Nix emulation. The amd64 default remains
unchanged. Seven focused tests passed; Ruff check, test-file format check,
Python compilation, and `git diff --check` passed. The retained M6 amd64 release
still passed `sync.py --check --release` after the source change.

- `tools/nix/flake.nix`: `e09a583b41f9ec56869661c80b1d5f8ca8c7c9e462530fe6bcccc2d81f6daabb`
- `tools/nix/flake.lock`: `8d29cda5426f0b81dce7f0dab87d59498d0bb4648e6ab80e611fa3525b66f7a7`
- `tools/internal/nix/prepare.py`: `d314a723b4dab6a1a082051d3bd7c886e60dce53582539f7516cbd5bc122c90e`
- M6 facade wheel: `eb5f63657cf15936ede2dda390e01389b79b3dbefe94a9ddcb14382b4445bbd0`
- ARM64 Ruff wheel: `b7d0906677d89bbf3cf73cde64b5bbe2ab35df3ae43e49ee2627301e91265bac`

## Platform and maintenance limits

`aarch64-darwin` evaluation retained all 15 versions and profiles; 14
Nixpkgs package records list that platform. OpenCode's custom derivation has
an explicit Darwin ARM asset and hash. macOS execution was not run. No native
ARM hardware claim is made.

One-time work is the cross-system preparation API repair and its regression
tests. Recurring ownership remains the Nix flake/lock and shared profile,
portable Bazel compatibility export through `sync.py`, platform asset hashes,
release identity, closure production/transfer, and profile activation.

Detailed candidate evidence and exact runtime commands are in
`experiments/tool-manager-nix/reference/README-m7.md`. Machine-readable evidence
is `/tmp/score-m7-nix/result.json`; raw logs remain in `/tmp/score-m7-nix/`.
No codex-1 CLI was exposed in this session; the M7 contract also forbids nested
CLIs/agents, so implementation and checks were done directly.
