<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# aqua: one Ruff decision, three consumers

2026-10-31. Bounded Round-3 comparison under the shared protocol. The ordinary
Python dependency requirement is now tested, rather than approximated by a
requirements-file runner. All files added in this round are in this directory;
previous experiments and production sources are unchanged. Nothing published.

## Result

**One authored aqua Ruff version selects all three outputs.** Native provisioned
Ruff actually runs; generated simple Bazel metadata selects the same version;
a standard Python facade wheel exposes that version to normal uv dependency
resolution. Both uv projects and uvx execute Ruff itself without aqua or a custom
runner on the consumer. The facade has no executable entrypoints or Python code.

| Local facade release | Authoritative aqua Ruff | Native `cp` executable | Generated Bazel version | Project `uv.lock` / `uv run` | Actual uvx |
| --- | --- | --- | --- | --- | --- |
| 0.1.0 | 0.11.13 | 0.11.13 | 0.11.13 | 0.11.13 | 0.11.13 |
| 0.2.0 | 0.11.12 | 0.11.12 | 0.11.12 | 0.11.12 | 0.11.12 |

The historical version decrease is merely a concrete change between available
versions. It is not a production downgrade recommendation. Facade name
`score-aqua-tools-probe`, release numbers and extra name are illustrative, not an
adopted public API. Local wheels stand in for immutable release artifacts.

## What is maintained, what is generated

- **Single Ruff authority:** [aqua.yaml](aqua.yaml), now at 0.11.12. The only
  authored Ruff change is one native version selection. Environment membership
  remains the tags in that same package entry.
- **Native resolved hashes:** [aqua-checksums.json](aqua-checksums.json), generated
  by aqua with checksum enforcement enabled. The
  [actual authored/hash diff](authoritative-and-hash.diff) separates the one
  authored line from three derived platform checksums.
- **Facade metadata:** [generate.py](generate.py) resolves the selected aqua
  version and writes ordinary static `pyproject.toml` with an optional Ruff
  dependency. [Generated metadata diff](generated-pyproject.toml.diff) shows both
  the derived Ruff dependency and the independent facade release-version change.
- **Simple Bazel metadata:** the same producer reuses the existing bounded
  [Ruff exporter](../export_ruff_multitool.py) unchanged in each temporary native
  snapshot. [Generated artifact diff](generated-ruff.lock.json.diff) shows the
  updated release URLs, hashes and extraction paths.
- **Release/package version:** supplied to generation as 0.1.0 or 0.2.0. That is
  a release identifier, not another maintained Ruff pin. Each generated snapshot
  records its native owner and selected version in `selection-*.json`.

Generated files visibly contain Ruff pins because native consumers and Python
resolvers need concrete metadata. They are outputs of one decision, not separate
hand-edited definitions. Generation freshness must be checked in real CI.

## Ordinary Python package mechanics

Generated package metadata uses the standard setuptools backend, no custom build
hook and no runtime loader for aqua configuration:

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"

[project]
name = "score-aqua-tools-probe"
version = "0.2.0"
requires-python = ">=3.10"
license = "Apache-2.0"

[project.optional-dependencies]
ruff = ["ruff==0.11.12"]

[tool.setuptools]
packages = []
```

This is the generated release-0.2.0 snapshot, not an additional authoring input.
`uv build --wheel` ran the normal backend with Python 3.12.3. A consumer or
standard build tool needs no aqua after this static package source is produced.
The wheel contains distribution metadata, no `entry_points.txt`, runner or code.
Its actual [METADATA](wheel-metadata-0.2.0.txt) includes:

```text
Provides-Extra: ruff
Requires-Dist: ruff==0.11.12; extra == "ruff"
```

The normal Ruff PyPI distribution supplies the executable. Its artifact can
vary from the native aqua archive while retaining the confirmed same-version
contract. This does not make native tools without a corresponding Python
distribution automatically available through uv.

## Actual commands and evidence

The prepared aqua 2.65.2 / uv 0.11.2 binaries and isolated caches from earlier
rounds were reused. Release sources/wheels and native exports remain under
`/tmp/score-aqua-round3/releases/{0.1.0,0.2.0}`. Illustrative generation flow from
this worktree, with the selected native input already at the desired state:

```sh
export AQUA_BINARY=/tmp/score-aqua-eval/bootstrap/aqua
export AQUA_ROOT_DIR=/tmp/score-aqua-eval/root
"$AQUA_BINARY" -c experiments/tool-manager-aqua/round3/aqua.yaml update-checksum --prune
python3 experiments/tool-manager-aqua/round3/generate.py 0.2.0 /tmp/release-source
"$AQUA_BINARY" -c /tmp/release-source/native/aqua.yaml cp --tags container -o /tmp/release-source/native-bin
uv build --wheel --python /usr/bin/python3 /tmp/release-source
```

For the before/after run, native 0.11.13 was generated/built first, then
`aqua -c .../aqua.yaml update ruff@0.11.12` changed the sole native selection and
the same refresh/generation/build steps produced the second release.
[Native/Bazel evidence](native-and-bazel-evidence.json) records direct native
commands, observed versions and matching generated artifact platforms. This
round did **not** rebuild or execute Bazel targets from the new snapshots; the
first-round real Ruff Bazel execution and round-two runtime proofs are reused.

A separate ordinary consumer project starts with no tool dependency and selects
only our facade release. For each wheel:

```sh
uv add --raw 'score-aqua-tools-probe[ruff] @ file:///absolute/release.whl'
uv lock
uv run --locked ruff --version
uvx --from 'score-aqua-tools-probe[ruff] @ file:///absolute/release.whl' ruff --version
uvx --with 'score-aqua-tools-probe[ruff] @ file:///absolute/release.whl' ruff --version
```

Use the actual versioned wheel filenames from the captured evidence rather than
literal `release.whl`. [Consumer evidence](consumer-evidence.json) preserves exact
argv/cwd/stdout/stderr/status for both releases and all commands. Consumer PATH
was `/usr/bin:/bin`; no aqua, mise or Nix executable was discoverable. A compatible
uv/uvx was explicitly supplied. No Container or Bazel was involved.

The saved consumer [before](consumer-0.1.0.toml) and
[after](consumer-0.2.0.toml) definitions contain only our facade extra and wheel
URI. Neither contains a copied Ruff dependency pin. The corresponding ordinary
[before lock](consumer-0.1.0.lock) and [after lock](consumer-0.2.0.lock) contain
Ruff 0.11.13 and 0.11.12 through normal dependency resolution. Updating the facade
selection changes the resolved Ruff package. There is no second environment
installed by our own hidden runner.

`uvx --from facade[ruff] ruff` actually succeeds, exit 0, but uv 0.11.2 warns that
the executable comes from dependency Ruff rather than the facade itself. The
normal alternative **`uvx --with facade[ruff] ruff`** succeeds for both versions
without that warning: the facade's ordinary dependency constrains the same uvx
resolution. This is not a workaround CLI or consumer Ruff pin. Preserve the
central facade selection rather than following the warning's suggestion to run
an unconstrained upstream Ruff package.

## Comparable complexity ledger

| Responsibility | Upstream/native machinery | Permanent repository responsibility demonstrated or remaining |
| --- | --- | --- |
| Tool decision | aqua native package selection and tags | Own the one Ruff selection and intended environments |
| Artifact selection | Pinned aqua registry, generated enforced hashes, native `cp` | Bootstrap/update registry and retain artifacts; no own native installer recipe for registry-covered Ruff |
| Python facade | Standard dependency/extra metadata and setuptools wheel building | Emit the selected Ruff version as a standard dependency; map exceptional Python distribution names where needed; verify generated metadata freshness |
| Native/Bazel compatibility | Existing Multitool format | Keep the bounded Ruff asset URL/archive-layout adapter; general layouts are not covered by this proof |
| Release production | Standard Python build tools consume the generated static source | Generate all outputs from one revision, assign facade release identity, build/retain the immutable distribution or commit generated source for Git consumption |
| Consumer execution | uv project resolver/lock/sync and uvx run Ruff's real executable | Consumer installs uv and selects our package/release; no aqua bootstrap, custom command or parser is required there |
| Image/native use | Native aqua export; previous fixed runtime proof | Put selected binaries/runtime at final prefixes with intended permissions; this round does not replace existing feature lifecycle |
| Consistency checks | Ordinary package metadata exposes resolved versions | Check native, generated Bazel and Python dependency agree; keep release artifacts synchronized and published metadata immutable |

`generate.py` is a bounded producer adapter, not a custom resolver or installer.
The copied first-round export script in temporary release sources is disposable
fixture plumbing; production would call one shared maintained exporter. Wheel
sources, consumer projects and capture scripts are also disposable probes. Real
integration must retain the named generation/build/release/check responsibilities,
not copy this temporary directory layout as architecture.

It is possible to invert authority and derive an aqua declaration from Python
metadata for tools available as Python distributions. This round did not evaluate
that alternative, and it would not eliminate native-only tool ownership. The
chosen model preserves aqua as the existing native owner and generates the uv
interface rather than maintaining two Ruff pins.

## Cross-candidate interpretation and remaining scope

The same standard facade-extra mechanism was shared with mise and Nix agents;
all three have reported successful normal uv project and uvx consumption. It is
not an aqua-specific capability advantage. The comparison now concerns the
producer: native owner/selection updates, artifact/recipe exports and build/release
integration. A facade avoids a consumer-side custom runner regardless of which
producer manager supplies the version.

**Tested:** two native versions, matching generated Bazel metadata, real standard
wheel building, ordinary uv project locking/execution and both native uvx forms
for both facade releases. **Reused:** previous direct prepared non-root Ubuntu
runtime and simple Ruff Bazel execution. **Untested:** new-snapshot actual Bazel
execution, real public artifact/Git release retrieval, production CI freshness
checks, broader distribution-name mapping and Mac execution. No full image,
universal converter or private package publication was required or attempted.

Reviewed the final mise and Nix round-three reports, their package generators,
authoritative changes and concrete export/consumer evidence. Both agents also
reviewed this report and generator; neither found a factual correction. Mise's
single TOML version change and Nix's already-locked package-set selection both
feed the same standard extra/Requires-Dist mechanism. Their Git-release fixtures
and this wheel fixture are release-form choices available to all three, not
manager capabilities. Wheels avoid consumer Git/source-build requirements;
source releases require the ordinary build backend, independently of manager.

The shared permanent costs are identity/layout mapping, standard metadata
export, freshness checks and release binding. Mise's common frontend does not
remove these adapters. Nix additionally derives portable upstream binary digests
rather than reusing a source hash; its selected store closure remains a distinct
native/container workflow. Both peer reports correctly separate newly inspected
Bazel metadata from earlier actual execution. None of these findings warrants
another Ruff integration case or establishes a measured maintenance winner.

## Primary specifications

- [Python project dependencies and optional dependencies](https://packaging.python.org/en/latest/specifications/pyproject-toml/).
- [uv dependency sources](https://docs.astral.sh/uv/concepts/projects/dependencies/).
- [uv tool execution](https://docs.astral.sh/uv/guides/tools/).
