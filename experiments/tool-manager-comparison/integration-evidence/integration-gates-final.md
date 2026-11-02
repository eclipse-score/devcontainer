<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Root M6 integration gates: final record

This concise summary is based on the result JSONs listed below, the final
Aqua coordinator report, and the root gate progress record. Result JSONs are
archived byte-for-byte. Earlier failed or interrupted result records remain
separate and are not counted as current passes.

## Latest completed results

| Candidate | Gate | Result |
| --- | --- | --- |
| mise | Root generic Node lifecycle | Passed: mise-node-lifecycle.final-result.json, run mise-lifecycle-20261102T005342Z-e45f699b; later interactive terminal check passed. |
| mise | Fresh published amd64 build and feature tests | Passed: mise-published-amd64.final-result.json, run mise-published-20261102T005520Z-30bf9722. |
| aqua | Root generic Node lifecycle | Passed: aqua-node-lifecycle.final-result.json, run aqua-lifecycle-20261102T010117Z-c25e6b4c; later interactive terminal check passed. |
| aqua | Fresh published amd64 build and feature tests | Passed: aqua-published-amd64.final-result.json, run aqua-published-20261102T012420Z-ee53ca4a. |
| nix | Root generic Node lifecycle | Passed: nix-node-lifecycle.result.json, run nix-lifecycle-20261102T002708Z-91ab1c48; later interactive terminal check passed. |
| nix | Fresh published amd64 build and feature tests | Passed: nix-published-amd64.final-result.json, run nix-published-20261102T004735Z-5b347540. |

The generic lifecycle checked the root generic Node Dev Container up/post-create
path and a later interactive terminal. The fresh published gate built for amd64
with cache-only output and appended the existing complete feature suite. The
suite ran as vscode in a login shell with HOME derived from the passwd entry.
This loads the feature's real profile configuration, including JAVA_HOME. No
built image was loaded or launched. Aqua's original unqualified gh --version
feature assertion is unchanged and passed on the final run.

All exact task builders and temporary workspaces were cleaned by the gate
runner. The archive excludes full logs, generated runtime payloads, and build
contexts; each result JSON is a compact status record.

## Preserved earlier attempts and corrections

- Mise's first root lifecycle failed when the PyPI backend could not discover
  uv nested under its install path. The source fix resolves the pinned
  executable and sets MISE_PYPI_UVX=true; a later lifecycle result passed.
  One intermediate retry was interrupted before a result was recorded.
- Aqua's first lifecycle completed up/post-create but failed the later shell
  check because the provisioned prefix was absent from the node user's PATH.
  The candidate now selects remoteUser node and exports the matching prefix;
  the later result passed.
- The first Nix lifecycle attempt was manually interrupted after oversized
  generated reference outputs were noticed. About 5 GiB remained, above the
  4 GiB automatic start floor; the automatic disk safeguard had not fired.
  The later recorded lifecycle passed.
- The initial Nix published feature run used a non-login harness shell, so the
  feature's actual JAVA_HOME profile was not loaded. The login-shell retry
  passed the unchanged suite.
- Mise's first published attempt failed before a candidate build because the
  temporary harness image name contained uppercase timestamp characters. The
  corrected lowercase-name build and suite passed.
- Aqua's first published attempt failed because a directly invoked helper was
  not executable. After its mode was corrected, a later suite run found an
  unselected Aqua-provided gh shadowing the expected APT gh. The provisioner
  now privately stages Aqua output and promotes only selected commands. The
  unchanged feature assertion passed on the final run.

The retained result records are named with initial, interrupted, or failure
suffixes. They document their actual status; the final six result records above
are the current gate outcomes.
