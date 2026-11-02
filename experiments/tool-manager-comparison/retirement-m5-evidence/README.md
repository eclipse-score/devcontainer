<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M5 installer removal evidence

Read the [comparison and conclusion](../../../docs/tooling-retirement-milestone.md)
and [common outcome contract](../retirement-milestone.md) first. All work is local
and uncommitted; each candidate retains its pre-existing M1–M4 changes. This is
the current code after removal, rather than the earlier package-feasibility audit.

## Recorded evidence

| File per candidate | Meaning |
| --- | --- |
| `*.before.json` | Static source snapshot captured before M5; all five installation/extraction functions and the old installation CLIs still exist |
| `*.after.json` | Final static audit: those functions/CLIs are absent, remaining module executable, caller/config candidates listed for review |
| `*.direct.json` | Five real direct-versus-strict prepared-command checks, including hostile PATH and a failing Ruff diagnostic with a spaced filename |
| `*.worker.md` | Candidate's exact provisioning, compatibility, update and other focused checks; maintenance ledger and pending gates |
| `*.sources.json` | SHA-256 and modes of files under the audited production roots, excluding generated payload/cache directories |
| `provenance.json` | Common HEAD, checkouts, runtime contexts, source/report identities and pending gates |

The after-audit Nix caller candidate is a **negative regression test** in
`tools/tests/test_catalog.py`: it invokes the removed CLI to assert that it is
unavailable. It is not a remaining installation route. The other two candidates
have no matching call/test candidates. All three retain the same six installer
commands: `environment`, `items`, `selected`, `shell-metadata`,
`verify-environment`, and `version`.

The mise/aqua production-to-experiment references are also reviewed: their
compatibility exporters still update a local generated reference pyproject.
Live version owners and feature/host provisioning no longer come from those
experimental directories. Final release packaging remains explicit follow-up
work, not an unreported duplicate owner or a completed publication flow.

## Reproduction

From the primary comparison checkout, for each candidate:

```sh
python3 experiments/tool-manager-comparison/retirement-audit.py \
  --repo ../score_devcontainer-eval-mise \
  --output /tmp/mise.retired.json --expect-retired
```

The audit is static and reports review candidates rather than equating a string
match with a live caller. Before snapshots were task-owned temporary source
copies, not a second Git revision. Their recorded installer hashes distinguish
them from the final source. Full source histories/payloads are not duplicated
in this evidence directory.

The actual host direct checks used the M5 installed trees:

```sh
python3 experiments/tool-manager-comparison/retirement-runtime-check.py \
  --candidate mise --repo ../score_devcontainer-eval-mise \
  --bin /tmp/score-m5-mise/provision-bin \
  --prefix-env SCORE_TOOLS_BIN_DIR --output /tmp/mise.direct.json
python3 experiments/tool-manager-comparison/retirement-runtime-check.py \
  --candidate aqua --repo ../score_devcontainer-eval-aqua \
  --bin /tmp/score-m5-aqua/host-tools/bin \
  --prefix-env SCORE_TOOLS_BIN --output /tmp/aqua.direct.json
```

For Nix, the same check ran in the existing public audit image
`score-execution-audit:20261102`, image ID
`sha256:efee32d02a8807af1b6556532b123749dd9bcb4a9a045e73c977db6acc978dc6`.
It used `--network none --read-only`, the normal host UID/GID and a writable
`/tmp` tmpfs. The M5 `release-amd64/native/nix/store` was mounted read-only at
`/nix/store`, current candidate source read-only at `/repo`, this common script
at `/check.py`, and the task output directory at `/work`. The script arguments
were:

```sh
python3 /check.py --candidate nix --repo /repo \
  --bin /nix/store/9h03gxnw4r3dxify1a043220qmf1ds9x-score-tools-repository/bin \
  --prefix-env SCORE_NIX_PROFILE_BIN --output /work/nix.direct.json
```

This checks current prepared execution, not host Nix installation or a fresh
published image. The worker report separately records actual profile creation
and upgrade in the Nix producer container. Task `/tmp` paths are local reusable
fixtures, not new production path requirements; use the documented candidate
provisioning command to create a new prefix on another machine.

## Limits

All real execution here is Linux amd64. Version differences between candidates
come from their selected owners; each direct/strict pair uses the same installed
tool. These checks do not compare startup speed across different versions and
are not exhaustive syscall traces. Previous trace evidence remains separate.

Fresh full M5 images, actual generic Node image lifecycle, ARM/macOS execution,
release hosting and hosted update/release automation remain pending. The first
Nix full-image attempt failed on a missing executable bit, which was fixed;
the final source has not passed a fresh full-image gate. Aqua's build attempt
was interrupted without completion. No old M3 image is relabeled as M5 proof.
