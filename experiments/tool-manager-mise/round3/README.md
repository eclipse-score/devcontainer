<!--
*******************************************************************************
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0

SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
*******************************************************************************
-->

# Round 3: one Ruff selection, ordinary uv dependency and uvx

2026-10-31. Applies the common round-three protocol and confirmed U5. No
production files changed, no global installation, publication or push. Package
name, extra names and release numbers below are experiment fixtures, not an API
proposal. The downgrade used for the before/after check is not an update policy.

## Result

**The newly required resolver-visible package path works.** One authoritative
mise Ruff declaration feeds native installation, the existing bounded Bazel
metadata export and generated ordinary Python package metadata. A consumer with
uv/Git/Python, without mise/aqua/Nix/Bazel/Container, resolves and runs Ruff through
both a normal project dependency and actual uvx.

| Observable | Local Git release `v0.1.0` | Local Git release `v0.2.0` |
| --- | --- | --- |
| Authoritative `mise.native.toml` | Ruff 0.11.13 | Ruff 0.11.12 |
| Actual native Ruff execution | 0.11.13 | 0.11.12 |
| Generated Multitool metadata version | 0.11.13 | 0.11.12 |
| Installed facade `Requires-Dist` | `ruff==0.11.13; extra == "ruff"` | `ruff==0.11.12; extra == "ruff"` |
| Ruff selected in consumer `uv.lock` | 0.11.13 | 0.11.12 |
| Actual project `uv run --locked ruff --version` | 0.11.13 | 0.11.12 |
| Actual `uvx --from ... ruff --version` | 0.11.13 | 0.11.12 |
| Actual `uvx --with ... ruff --version`, without warning | 0.11.13 | 0.11.12 |

[evidence.json](evidence.json) captures exact commands, stdout/stderr, commits,
consumer metadata and the results. The producer lives in an independent local
Git fixture recorded in [state-path.txt](state-path.txt); only that disposable
repository receives local commits/tags. No inherited documentation was committed.

## Authoritative input and generated files

The producer fixture starts as a copy of the existing experiment's native
configuration. The **only Ruff version selection** is:

```toml
[tools]
"aqua:astral-sh/ruff" = "0.11.13"
```

For the second release, the existing mise command changes it to 0.11.12 and
refreshes the native lock. [authoritative.diff](authoritative.diff) shows that
single decision. [generated.diff](generated.diff) shows the lock, Bazel metadata
and Python package metadata following it. No Python-specific Ruff pin is edited
independently. The package release number changes separately to identify the
producer's release; it is not another Ruff version authority.

The unchanged existing Ruff exporter is copied into the disposable producer and
run against that release's config/lock. It retains the previously disclosed
Ruff archive-layout rule. Its generated Bazel metadata is inspected, not rebuilt
through Bazel in this round. Native actual Ruff execution uses the earlier
explicit-release harness. Container/runtime proof for both selected versions
already exists in round two; no full image rebuild is repeated.

`generate-package.py` reads the authoritative TOML, then writes static ordinary
metadata. The generated package has **no Python module and no entrypoint**:

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "score-tools-probe"
version = "0.1.0"
requires-python = ">=3.10"

[project.optional-dependencies]
ruff = ["ruff==0.11.13"]

[tool.setuptools]
packages = []
```

That Ruff dependency is generated from the native pin, not a second maintained
selection. Committed static metadata makes the consumer's standard build require
only setuptools/Python, not mise or the generator. Ruff's ordinary distribution
supplies the actual Ruff executable; no wrapper installs a hidden environment.

## Normal downstream project and uvx consumption

The temporary consumer starts with an ordinary empty uv project. For each local
Git release it executes, with `RELEASE` identifying only our package/tag:

```sh
uv add --raw 'score-tools-probe[ruff] @ git+file:///ABS/producer@RELEASE'
uv lock --check
uv sync --locked
uv run --locked ruff --version
uvx --from 'score-tools-probe[ruff] @ git+file:///ABS/producer@RELEASE' ruff --version
uvx --with 'score-tools-probe[ruff] @ git+file:///ABS/producer@RELEASE' ruff --version
```

The commands really run for both tags with uv/uvx **0.11.2**, Python
`/usr/bin/python3`, and isolated task caches. The consumer PATH contains only
`/usr/bin:/bin`; uv and uvx are invoked through explicit prepared binary paths.
No producer manager is present or called in the consumer build/execution path.

The generated consumer `pyproject.toml` contains only the facade requirement
with its release tag and Ruff extra. Its `uv.lock` records Ruff as a normal
resolved package, and the installed facade's standard `Requires-Dist` contains
the exact selected version. The test asserts all three observations, rather than
inferring dependency resolution from a successful command alone.

Before/after [snapshots](before/consumer.pyproject.toml) and
[updated snapshots](after/consumer.pyproject.toml) preserve the facade package
metadata, consumer inputs/locks and native Bazel metadata for inspection.
The lock contains resolver-generated Ruff pins; the downstream author never
copies or maintains them as an independent requested version.

**Observed `--from` uvx warning** (uv 0.11.2, retained in evidence):

```text
warning: An executable named `ruff` is not provided by package `score-tools-probe` but is available via the dependency `ruff`. Consider using `uvx --from ruff ruff` instead.
```

It nevertheless installs both normal packages, executes real Ruff and exits 0.
The aqua peer identified the better native form: `uvx --with 'FACADE[ruff] @
RELEASE' ruff --version`. I also executed this for **both local Git tags**:
0.11.13 and 0.11.12, exit 0, **no warning**. Ruff is the executable's primary
package and the facade's dependency constrains it in the same uv resolver;
consumers still do not provide a Ruff version. No custom CLI or warning
suppression is needed. Both actual command forms remain in evidence; `--with`
is the cleaner observed UX for this illustrative metapackage shape.

## Comparable complexity ledger

| Responsibility | Ongoing owned piece | What is already supplied upstream / what is only a fixture |
| --- | --- | --- |
| Version and membership decisions | Maintain direct native/Python configuration and selected environments; one Ruff owner | mise owns its config syntax and installer/backend orchestration |
| Native locks and installation | Choose supported targets and lock/provenance policy; run the normal refresh/install sequence | mise/aqua backend owns downloading/extracting recipe-covered native tools |
| Existing simple Bazel interface | Retain bounded metadata export, archive-layout/name mappings and registration checks | Existing Multitool format/runtime; no general exporter or complex packaging framework built |
| Resolver-visible Python export | Map applicable native tool identity to PyPI distribution/extra and generate static dependency metadata from the selected pin | Standard setuptools build and dependency/extra metadata; no custom runtime launcher |
| Build/release pipeline | Refresh locks, regenerate both exports, detect drift, commit generated metadata or distribute built wheels with an immutable selected release | Git/ordinary Python build tools; exact production Git subdirectory/wheel delivery remains undecided |
| Consumer project | Select the producer release/extra; normal uv lock/sync/run | uv resolves the actual Ruff dependency and supplies its executable |
| Consumer uvx | Select the same producer release/extra via `--with`, with Ruff as the tool | uvx resolves the facade pin and runs Ruff without warning; `--from` also works with the disclosed warning |
| Optional convenience command | Separate UX choice; does not own versions or replace dependency metadata | Not implemented or required by this experiment |

The permanent new piece for U5 is the **producer-side static dependency export
and release wiring**, not a consumer installer. For Ruff it reads a single native
version and knows that its Python distribution/entrypoint is named `ruff`.
Other tools can need explicit identity mapping or may lack a suitable Python
distribution; this probe makes no universal PyPI-delivery promise.

The production workflow must bind the native lock and generated Bazel/Python
outputs to the same release and validate drift. Static generated metadata was
chosen deliberately so consumers need neither mise nor a bespoke build plugin.
The disposable `probe.py`, release-copy directory, test tags and evidence copies
are verification machinery, not three new production abstractions. Prototype
file/line counts and one-manager branding are not maintenance scores.

Compared with aqua plus uv, the Python package mechanism is now the same shared
standard export. mise's native orchestration does **not** remove this U5
responsibility. Nix can likewise export its selected package version into the
same metadata; its package-set/closure choices remain separate responsibilities.
The earlier idea that direct mise execution alone could eliminate the public
Python adapter no longer satisfies the confirmed requirement and is not used as
a comparative advantage here.

## Evidence classification and remaining scope

| Item | Classification |
| --- | --- |
| Before/after native Ruff version | **Tested**, real execution of both selected versions |
| Native/container installed-runtime approach | **Reused tested evidence** from round two, including changed-version runtime execution; no new image build |
| Before/after Bazel version/platform artifact selection | **Generated and inspected**; existing known Ruff layout reused, no new Bazel execution claimed |
| Standard package build/dependency metadata | **Tested**, consumer builds local Git releases with setuptools and installed `Requires-Dist` matches |
| Normal uv dependency, lock and Ruff invocation | **Tested** for both producer releases, consumer maintains only facade release/extra |
| Actual uvx Ruff invocation | **Tested** for both releases: `--from` with warning and native `--with` without warning |
| Exact public package name/API/distribution, complete catalog exporter | **Not implemented**; illustrative choices are not commitments |
| macOS ARM execution, full production image and historical retention | **Unchanged gaps**, outside this focused package probe |

Reproduce with `python3 experiments/tool-manager-mise/round3/probe.py` after the
previous isolated mise bootstrap. It creates fresh temporary release/consumer
fixtures and preserves evidence here. No package is published. See the official
[uv dependency guidance](https://docs.astral.sh/uv/concepts/projects/dependencies/)
and [uvx sources/extras guidance](https://docs.astral.sh/uv/guides/tools/) for the
standard mechanisms used, rather than a custom execution protocol.

## Completed peer review

Both final sibling round-three reports and their concrete configs, generators,
authoritative/generated diffs and consumer evidence were read. Review feedback
was sent directly to both agents; no conflicting capability or ownership claim
was found.

- **aqua:** its native owner, enforced checksum refresh and bounded Ruff exporter
  remain distinct from the new standard package metadata/build/release work.
  Both wheel-based uv dependency states and warning-free `uvx --with` are recorded.
  A wheel consumer avoids the Git/source-build prerequisites of our fixture;
  wheels versus Git are release-distribution choices available to all candidates.
- **Nix:** its package-set selector and runtime closure handoff remain distinct
  responsibilities. Its portable Bazel exporter additionally obtains upstream
  binary digests, which Nix source hashes do not supply. Its report correctly
  labels this generated metadata, not a new Bazel or archive-validation run.
  Static facade metadata makes consumer Nix unnecessary; the fixture's Python
  3.14 choice is disclosed rather than promoted to a product requirement.
- **Shared conclusion:** all three demonstrated normal resolver-visible package
  dependencies and both native uvx forms. The producer must still own identity
  mappings, generated-output freshness and immutable release wiring. Neither a
  single manager name nor the working metapackage removes those responsibilities.

No architecture winner is selected by this report.
