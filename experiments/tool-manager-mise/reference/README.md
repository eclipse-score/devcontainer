<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Current result

M5 completes the direct-provisioning migration and removes the replaced native
and Python install engine. See [README-m5.md](README-m5.md) for the removal and
maintenance ledger, exact checks, and platform limits. The milestone reports
below are historical snapshots.

Production ownership and update entry points now live in `tools/mise/` and
`tools/internal/mise/`. This experiment directory retains only local release
fixtures and historical evidence; Renovate ignores it.

# Mise M2: actual repository integration

Completed locally 2026-11-01; retained functional evidence was captured before
the quota interruption. All required paths passed. This extends the maintained
M1 producer into **real checkout consumers** rather than another synthetic
module. No manager has been selected, and no changes were published.
[M1's historical report](README-m1.md) describes its earlier three-tool scope;
its no-uv/ShellCheck-selection assumptions are superseded here.

## What changed outside experiments

- Seven real `tools/lockfiles/*.lock.json` snapshots now derive actionlint,
  bazelisk, buildifier, Ruff, ShellCheck, uv/uvx and yamlfmt from native mise
  owners. Existing descriptions, schema metadata, command identities and public
  targets are retained; unmigrated lockfiles are untouched.
- `tools/score_tools/python_tools.bzl` retains the existing data-only catalog
  contract/descriptions and derives pre-commit, pytest and basedpyright pins.
- `tools/environments.json` repository native/Python fields are generated from
  resolved active repository tools, preserving npm and every other profile.
  Their values happen to match baseline, so this ownership change creates no
  file diff there.
- Existing root `MODULE.bazel`/`tools/BUILD.bazel`, `tools/run-tool` and
  `.pre-commit-config.yaml` consume those outputs unchanged. Their **actual**
  Bazel targets, wrapper modes and hooks were executed.
- The conflicting direct uv Renovate regex was removed; uv/uvx and its Bazel
  helper now share **one native uv pin**. `tools/README.md` documents regeneration
  and its generated inventory is current.

## Source ownership and exact selections

`mise.native.toml` owns the shared native versions; `mise.python.toml` owns
pre-commit. The native env composition in `provision.py` makes repository use
those shared inputs, while published additionally loads `mise.published.toml`.
That file owns pytest/basedpyright. No second authored membership/version table
was introduced. Native generated locks cover Linux x64/ARM64 and macOS ARM64;
only Linux x64 execution is claimed.

| CLI | Default repository | Default published | Isolated update |
| --- | --- | --- | --- |
| actionlint | 1.7.7 | 1.7.7 | unchanged |
| bazelisk | 1.27.0 | 1.27.0 | unchanged |
| buildifier | 8.2.1 | 8.2.1 | unchanged |
| Ruff | 0.11.13 | 0.11.13 | 0.11.12 |
| ShellCheck | 0.10.0 | 0.10.0 | unchanged |
| uv and uvx | 0.13.6 | 0.13.6 | unchanged, one release decision |
| yamlfmt | 0.17.0 | 0.17.0 | unchanged |
| pre-commit | 4.7.0 | 4.7.0 | unchanged |
| pytest | excluded | 9.0.2 | unchanged |
| basedpyright | excluded | 1.35.0 | unchanged |

The existing `.bazelversion` remains the sole selected Bazel 8.6.0 owner.
The historical Ruff downgrade is an independent-update fixture, not a proposed
production downgrade. basedpyright's ordinary PyPI dependencies supplied
`nodejs-wheel-binaries` 24.19.0 during provisioning; no separate Node pin or
custom Node packaging was added.

## Reproduce

Producer prerequisites remain isolated mise 2026.10.24, Python 3.12+, Git and
network access; Docker builds the tooling images. The existing checksummed
`bootstrap.sh` installs mise into an explicit private directory. Consumer checks
add existing uv/uvx and Bazel executables; no global manager installation is used.

```sh
bash experiments/tool-manager-mise/reference/bootstrap.sh /tmp/private-mise
export MISE_BINARY=/tmp/private-mise/mise
export SCORE_MISE_REFERENCE_STATE=/tmp/private-mise-tools
python3 experiments/tool-manager-mise/reference/prepare.py /tmp/fresh-mise-release --version 0.3.0 --root write
python3 experiments/tool-manager-mise/reference/check.py /tmp/fresh-mise-release /tmp/fresh-mise-evidence --build-images
python3 experiments/tool-manager-mise/reference/prepare.py /tmp/fresh-mise-release --root check
python3 tools/internal/sync_readme.py --check
```

Use fresh release/evidence directories. The captured baseline release lives at
`/tmp/score-mise-m2/releases/0.3.1`; its standard package version is 0.3.0 (the
local directory/image label is only a fixture identifier). The update is at
`/tmp/score-mise-m2/releases/0.4.0`, package version 0.4.0. Explicit `--source`
supports an isolated owner update without changing the checked-in default.

`prepare.py` snapshots current native owners, resolves native locks, generates
ordinary static setuptools extras and real-root compatibility outputs, and
retains complete installed tool/venv trees in the release. `install.sh` exposes
the selected tools at their preserved canonical prefixes. Producer-installed
paths in the captured reference are below `/tmp/score-mise-evaluation-fresh`;
the release **copies their complete contents**, so images do not depend on those
external paths remaining on the host. Python runtime ABI is Ubuntu Python 3.12.
The packaging prefix/base-runtime policy remains a production adoption decision.

`check.py --phase root|hooks|uv|images` permits targeted retries through the same
maintained implementation. Root/all checks validate current native owner
snapshots before comparing real generated consumers. uv/image checks can consume
an explicitly selected older immutable release independently of today's root.
Root writes/checks do not mutate release snapshots.

## Actual acceptance and evidence

[evidence/m2/](evidence/m2/) retains compact exact argv/cwd/status/stdout/stderr
records, owner/generated diffs, real consumer pyprojects/locks/Requires-Dist,
expected versions, image IDs and full shared image-check output. Runtime trees,
image layers and Python environments remain outside Git.

| Path | Default result | Updated result |
| --- | --- | --- |
| Real ROOT Bazel | All eight native CLI targets and pre-commit executed at exact versions | Same targets executed, Ruff .12 observed |
| ROOT module checks | `mod deps --lockfile_mode=error` and `mod tidy` passed | Both passed |
| Existing real repository hooks | Ruff format/check on `tools/score_tools/catalog.py`; ShellCheck on `tools/run-tool`; yamlfmt on `.pre-commit-config.yaml`; buildifier on `tools/BUILD.bazel`; actionlint on `.github/workflows/ci.yaml` passed | Root updated Ruff execution observed; unchanged hooks were not gratuitously repeated |
| Ordinary uv/uvx | Repository two Python CLIs and published four CLIs resolve normally, exact locks/Requires-Dist, actual versions | Same, Ruff dependency changed to .12 |
| Useful published Python work | Real pytest assertion passes; basedpyright reports intentional `reportAssignmentType` | Both pass again |
| Real COPY images, repository and published | Both shared checks passed as uid12345 with network denied | Both passed again |
| Actual image `tools/run-tool` | Every selected CLI direct, convenience and strict mode observed | Same for updated selection |
| Update drift | Stale old release rejected against changed current owner; freshly generated Ruff/facade drift detected before applying | Regeneration passes; other versions/native artifacts unchanged |

The ordinary package has no application module, installer or custom entrypoint.
Generated extras cover Ruff/pre-commit/pytest/basedpyright only; no artificial
Python delivery of native-only tools was added. Consumers select the release
wheel/extra, not copied tool pins. Both `uv run` and warning-free native
`uvx --with` execute actual upstream commands in the standard resolver.

`Dockerfile` performs COPY plus the maintained installer, not cache bind mounts.
It warms the Bazel selected by the existing `.bazelversion` online as uid12345.
The unchanged shared M2 script is mounted only as test input with expected
versions and the real checkout `tools/run-tool`; installed tooling comes from
image layers. uv/uvx and ShellCheck are deliberately present in repository;
pytest/basedpyright are absent there. No mise/aqua/Nix command is on image PATH.
These are real Ubuntu tooling images, not full outer Node/Docker DevContainers.

## New integration findings

- **Bazelisk needs a recognized workspace.** Merely placing `.bazelversion` in
  a bare directory initially warmed latest Bazel instead of 8.6.0. A generated
  empty `MODULE.bazel` marker fixes image warmup and the shared consumer fixture;
  there is no second handwritten Bazel pin. The resolved image checks prove
  actual offline Bazel 8.6.0 execution.
- **Artifact identity differs from CLI identity.** mise's aqua registry resolved
  old `bazelbuild/buildtools/buildifier` to `bazel-contrib/buildtools` URLs.
  Exporting resolved native-lock URLs handled this without another repository
  alias pin. Raw binaries and archive member layouts still need bounded mappings.
- **Runtime assembly cannot copy console scripts alone.** Full venv trees and
  absolute prefixes are retained; basedpyright's Node wheel is included naturally
  in that runtime rather than packaged by a new subsystem.
- **Real root ownership includes membership and update automation.** Deriving
  locks alone would leave post-create's repository membership and the uv Renovate
  rule as competing owners. Compatibility membership output and rule removal
  address those boundaries.
- The shared Buildifier fixture initially assumed one exact line layout. It was
  corrected to verify changed, semantically equivalent, accepted Starlark rather
  than treat a valid multi-line BUILD format as a candidate failure.

## Remaining integration ownership and limits

| Responsibility | What upstream supplies | What remains ours |
| --- | --- | --- |
| Tool versions/membership | Native mise envs and installers | Direct selections, profile composition and platform policy |
| Native resolution | mise/aqua recipes and generated artifact locks | Refresh/provenance/retention policy |
| Existing real ROOT consumers | Multitool plus unchanged Bazel/Python/cwd adapters | Bounded archive/command mappings, metadata export, repository membership compatibility and drift assertions |
| Standard Python interface | setuptools metadata and uv resolver/CLI execution | Native-to-PyPI name mapping, static extras and release binding |
| Tooling images | Ubuntu base, native installed trees/venvs | Complete prefix/ABI preservation, installer sequencing, Bazel warmup and non-root checks |
| Adoption | Existing feature/APT and outer image lifecycle | Remaining catalog migration, OS/feature ownership, automation, downstream compatibility and artifact retention |

The full inherited pre-commit `--all-files` suite was intentionally not run over
historical experiments. Required real local hook IDs were run individually;
root Bzlmod checks ran separately. Applicable changed-source lint/license checks
are recorded separately. Cold offline Bazel/PyPI setup, compiler-free initial
Python tool bootstrap, macOS execution, external CI and complete production
image migration are not claimed.

Final state restores real root outputs and facade to the checked-in default
Ruff .13 owner; update diffs/evidence remain separate. Default drift and generated
README checks pass. There is no invented migration percentage or manager winner.

## Direct M2 peer review

Reviewed actual aqua/Nix root diffs, native owners, sync/drift implementations and
Dockerfiles, not only their reports. Both derive the migrated native/Python
versions and repository membership while preserving unrelated consumers. Nix
retains a full store closure and separately resolves portable release digests;
aqua retains its native tags/Python groups and fixed target-ABI venv. Their
Bazel choices derive from the same existing `.bazelversion`.

Both peers reviewed this root integration without a functional objection.
Aqua's metadata review caught that `$schema` should be preserved; the exporter
and root compatibility normalization now retain it (no unsupported `$comment`).
No additional comparative test round was needed.
