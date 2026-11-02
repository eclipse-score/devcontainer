<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M8 release-workflow evidence

All three source-worker turns completed. Each produced A 0.8.0 from its current
owners and B 0.8.1 with Ruff 0.14.6 from an isolated maintained-source owner
change. Current candidate owner pins stayed unchanged. The evidence covers
stale rejection/refresh, owner-bound ordinary wheel handoff, the same uv project
and native installation updated A to B, ordinary uvx, and an actual updated
public Bazel Ruff invocation. Fixture identities are local, not adopted APIs.

## Independent review and source continuity

- [Root source/unit/artifact review](root-review.json) and
  [actual wheel/consumer-lock review](artifact-review.json).
- [Source-change summary](source-change-summary.md),
  [accepted-owner continuity](owner-continuity.json), and
  [M8 starting hashes/modes](source-before.json).
- [Source and archival provenance](provenance.json).

Root's artifact review reads actual wheels and locks; it is not a new runtime
execution. Source-worker runtime results retain their exact conditions.

## Candidate reports and required edits

| Evidence | Mise | Aqua + uv | Nix |
| --- | --- | --- | --- |
| Final report | [Handoff](mise/final.md), [candidate README](mise/README-m8.md), [result](mise/result.json) | [Handoff](aqua/final.md), [candidate README](aqua/README-m8.md), [result](aqua/result.json) | [Handoff](nix/final.md), [candidate README](nix/README-m8.md), [result](nix/result.json) |
| Owner edit | [Exact diff](mise/authored-owner.diff.json) | [Exact diff](aqua/authored.diff.json) | [Owner-scope diff](nix/authored-owner.diff.json): flake selection authored; flake.lock generated |
| Generated compatibility output | [Diff](mise/generated.diff.json) | [Diff](aqua/generated.diff.json) | [Diff](nix/generated.diff.json) |
| Wheel metadata A / B | [A](mise/a-wheel-METADATA.txt), [B](mise/b-wheel-METADATA.txt) | [A](aqua/METADATA-A.txt), [B](aqua/METADATA-B.txt) | [A](nix/wheel-a-METADATA.txt), [B](nix/wheel-b-METADATA.txt) |
| Same-project authored input A / B | [A](mise/consumer-a.toml), [B](mise/consumer-b.toml) | [A](aqua/consumer-A.toml), [B](aqua/consumer-B.toml) | [A](nix/consumer-a.toml), [B](nix/consumer-b.toml) |
| Resolver locks A / B | [A](mise/uv-a.lock), [B](mise/uv-b.lock) | [A](aqua/uv-A.lock), [B](aqua/uv-B.lock) | [A](nix/uv-a.lock), [B](nix/uv-b.lock) |
| Native update proof | [A](mise/native-a.json), [B](mise/native-b.json), [prepared calls](mise/native-b-calls.json) | [A](aqua/native-A.json), [B](aqua/native-B.json), [commands](aqua/commands.json) | [Profile/calls](nix/native-commands.json), [closure binding](nix/closure-check.json) |
| Public Bazel proof | [Structured result](mise/result.json), [selected artifact](mise/b-generated-ruff.lock.json) | [Commands/results](aqua/commands.json) | [Commands/results](nix/bazel-commands.json), [selected artifact](nix/bazel-selection.json) |

Unified diffs are stored as JSON with exact UTF-8 patch text in `text` to
preserve context whitespace through repository checks. Decoding that field
reproduces the original source hash. Reports are copied exactly except SPDX
headers where missing and source-link rebasing to their original worktree.

Absolute scratch/source paths in reports refer to the original local fixtures.
Transcripts are not idempotent replay scripts: use fresh release/check outputs
and reproduce the owner change at the stated A/B boundary. No runtime trees,
wheels, full logs or maintained-source copies are archived. Every artifact is
below 50 KiB; source paths, original and archived hashes, and transformations
are recorded in provenance.
