<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M8 source changes and recurring duties

The [independent root review](root-review.json) records exact source-start and
final hashes, deletions and inventoried modes; its [artifact review](artifact-review.json)
inspects actual wheels and consumer locks. Root independently reran the four
Mise and nine Nix affected unit tests. Runtime execution is the source workers'
recorded execution, not an additional independent runtime rerun.

- **Mise:** explicit stale owner/lock rejection replaces an optimization-sensitive
  assertion in `refresh.py`; targeted regression covers normal and optimized
  Python. Four affected unit tests and the corresponding Bazel test passed.
  `tools/README.md`, `tools/internal/README.md` and the existing maintained
  `tools/internal/mise/README.md` consolidate the supported sequence and remove
  superseded Git-wrapper/fixed-release snippets. Required helpers remain.
- **Aqua:** no implementation repair. `tools/internal/README.md` points to the
  new maintained `tools/internal/aqua/README.md`. No exercised helper was
  demonstrated redundant. Missing staging configuration was a fixture setup
  correction; traceback-style stale reporting and cache-backed recopy/reinstall
  remain documented API properties.
- **Nix:** optional immutable-store hardlink reuse and two focused regression
  tests were added to `prepare.py`/`test_prepare.py`. Directories and mutable
  release metadata remain independent; reuse requires trusted immutable files
  and the same filesystem. This is storage/release efficiency, not a required
  migration repair. The obsolete `tools/internal/nix/Dockerfile` and its export
  were removed; fresh preparation still produced the required release outputs.
  `tools/internal/README.md` and the new `tools/internal/nix/README.md` describe
  the supported sequence. Package-only generation and focused smoke/membership
  helpers remain useful; preparation already generates facade metadata.

[Owner continuity](owner-continuity.json) independently checks accepted owners.
The bounded source-start inventory omits `tools/nix/flake.nix`; its final content
matches the accepted M7 Nix source digest. All other recorded owner hashes match
the M8 start inventory. Inventoried modes are unchanged. A/B authored release
fixtures and generated outputs are separate from these candidate source changes.

The required owner edit differs by manager: a direct native version in Mise or
Aqua, versus a Nix input/derivation selection with a generated flake lock. The
known historical Nixpkgs snapshot was supplied; arbitrary-version discovery is
not established. Native Nix closure generation serves native delivery and is
separate from the ordinary wheel output/consumer requirements. Source changes,
setup fixes, optional storage reuse, release operations and per-platform package
availability checks are not interchangeable measures of maintenance cost.
