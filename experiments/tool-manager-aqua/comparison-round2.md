<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# aqua + uv: common comparison, round two

2026-10-31. Follows the parent's agreed C1/C2/C3 protocol. No production changes,
global installs, pushes or publication. This evaluates outcomes and maintenance
ownership, not config/line/test counts. See [peer review](peer-review.md) for the
agreed criteria and corrections to first-round interpretations.

## Outcome

**C1, C2 and C3 passed for the bounded selections.** Two ordinary backend configs
are enough for these cases: aqua's native manifest for native CLIs and uv's
requirements input for Python. No extra universal schema or general cwd-restoring
runtime wrapper was needed. This does not mean a production release interface,
installer/update pipeline and complete catalog migration already exist.

| Check | Tested result | Evidence |
| --- | --- | --- |
| C1 independent update | Ruff 0.11.13 → 0.11.12 executes; pre-commit remains 4.7.0. Only aqua's native pin changed; requirements bytes unchanged; hashes regenerated. | [Results](round2/c1-results.json), [actual input/output diff](round2/c1-update.diff) |
| C1 selections/add/remove | actionlint added only to repository-tagged native selection. Fresh container export excludes it, repository export includes it. After deleting the entry, fresh repository export excludes it. | [Results](round2/c1-results.json) |
| C2 host caller contract | Both real selected tools execute from a temporary consumer checkout; false same-name PATH executables and consumer aqua/Python config do not override selection. Caller cwd, spaced arguments, Ruff diagnostic and pre-commit error status observed. | [Fixture](round2/consumer_fixture.py), [host results](round2/c2-results.json) |
| C3 prepared direct runtime | Both real tools execute directly under Ubuntu Python 3.12.3 as uid 12345 with `--network none`, read-only prepared prefix and no manager/runtime installer on PATH. Same behavioral fixture passes. | [Setup log](round2/c3-setup.log), [run command](round2/c3-command.json), [runtime results](round2/c3-results.json) |
| C1 → C3 targeted update propagation | C1's actual Ruff 0.11.12 export also executes in the same Ubuntu/user/network conditions alongside unchanged pre-commit 4.7.0. | [Targeted update results](round2/c1-c3-update-results.json) |

The full C2/C3 behavioral fixture uses the baseline release selection
0.11.13 / 4.7.0. The final row is a targeted version/startability check of C1's
changed output, **not** a repeated full fixture or proof of a generic deployment
pipeline. Existing first-round Bazel evidence remains separate.

## C1: actual maintainer workflow

A temporary copy at `/tmp/score-aqua-round2/c1` retained all authoring formats:

```sh
aqua -c aqua.yaml update ruff@0.11.12
aqua -c aqua.yaml update-checksum --prune
aqua -c aqua.yaml cp --tags container -o changed
changed/ruff --version
changed/uv run --no-project --no-config --isolated \
  --with-requirements requirements.txt pre-commit --version
```

Observed 0.11.12 / 4.7.0; the saved diff shows the one native pin change and three
regenerated Ruff checksums. To exercise missing first-round selection evidence:
`aqua generate -i rhysd/actionlint@v1.7.7` added the native declaration; its one
entry received `tags: [repository]`. After `update-checksum --prune`, fresh
`cp --tags container` exported Ruff/uv/uvx and fresh `cp --tags repository` also
exported actionlint. Deleting that final package entry, pruning hashes, and
exporting to a new directory removed actionlint from the intended repository
output. Version pins were not copied into an independent environment manifest.

Membership changes do not uninstall old cache/output files automatically; fresh
image construction or explicit cleanup is still an installer responsibility.
The Python selection in this bounded probe is shared by both environments; no
unnecessary additional Python profiles were invented.

## C2: host execution from an unrelated consumer

The tested native entrypoint is the ordinary aqua command with explicit config:

```sh
aqua -c /absolute/selected-release/aqua.yaml exec -- ruff ...
```

The Python route is the ordinary uv command using the selected requirements:

```sh
uv run --no-project --no-config --isolated \
  --with-requirements /absolute/selected-release/requirements.txt pre-commit ...
```

After the described preparation, `round2/run-host.sh` reproduces this fixture.
The actual invocation arrays are captured in the JSON evidence. The fixture
creates a temporary Git checkout with a directory/file containing spaces, a fake
`ruff` and `pre-commit` at the front of PATH (exit 99), a conflicting `aqua.yaml`
and `pyproject.toml` requesting other versions. The actual selection reports
Ruff 0.11.13 and pre-commit 4.7.0. Ruff reads relative `file with spaces.py` and
returns F401/exit 1. A local pre-commit system hook records the consumer cwd and
arguments `two words` and `--literal=one two`, then exits 7. pre-commit returns
its own expected exit 1; the host command preserves it.

Prepared aqua state and uv cache from round one were reused. Bootstrap is still
required: aqua for native host execution; a compatible uv for the Python-only
route; a selected release's configs must be retrieved and their absolute paths
known. The test used explicit prepared aqua/uv binary paths to avoid substituting
host tools; a public release locator/bootstrap wrapper is not implemented here.

A convenient single `run-tool` product command can dispatch these two native
invocations. It still needs command validation, selected-release/config lookup
and errors, but no observed cwd-restore step or catalog parser was required for
this tested route. An exact Git-package `uvx ... score-tool` interface remains
additional release packaging work, equally as in the other probes.

## C3: Ubuntu runtime preparation and direct non-root execution

Common base:
`score-tool-manager-comparison-base:20261031`, image ID
`sha256:1b1ebf493ffb1a5a3a4d3c4c2a822cfe0da563d7028159078b0a02a12122a28d`.

Preparation uses the same authoritative native export and requirements input.
The host prefix `/tmp/score-aqua-round2/runtime` is mounted at the fixed path
`/opt/score-tools`; Ruff is copied into `bin` from aqua's selected export.
A preparation container runs as root with network and transient uv mounted at
`/tmp/uv`:

```sh
/tmp/uv venv --python /usr/bin/python3 /opt/score-tools/python
/tmp/uv pip install --python /opt/score-tools/python/bin/python \
  -r /tmp/requirements.txt
chmod -R a+rX /opt/score-tools
```

The requirements file is mounted read-only from this experiment. The interpreter
is the **base image's Python 3.12.3**, not the host's 3.14 interpreter. The venv's
entrypoint records its stable `/opt/score-tools/python` path. No production image
or other repository content was copied.

Runtime uses that prepared prefix read-only, the fixture script read-only, uid
12345, `--network none`, and writable default user home/temporary directories.
The exact command is in `c3-command.json`. It first rejects any aqua/mise/Nix/uv
on PATH, then uses direct commands:

```sh
/opt/score-tools/bin/ruff ...
/opt/score-tools/python/bin/pre-commit ...
```

Both versions and the same relative-file/cwd/argument/failing-hook fixture pass.
No package manager or bootstrap installer executes during tool use. The venv
and supporting installed packages remain; system Python must remain compatible
with the fixed-prefix venv. This is valid prepared installation evidence, not a
claim of arbitrary venv relocation or ten-year reproducibility.

For the targeted C1 update check, C1's actual changed Ruff executable was copied
to `runtime/updated/ruff` and directly executed under the same image/user/network
conditions. It reports 0.11.12; the unchanged prepared pre-commit reports 4.7.0.

## Maintenance ownership after functional parity

| Responsibility | aqua + uv approach actually demonstrated | Still ours |
| --- | --- | --- |
| Direct version selection | Native aqua config plus Python requirements; no duplicated maintained pin | Decide selected tools/release and review updates |
| Native artifact recipe/platform/hash resolution | aqua registry + generated enforced checksums | Bootstrap aqua, pin/update registry, keep hashes/artifacts and handle missing registry recipes |
| Python resolution/installation | uv reads requirements and prepares fixed venv or isolated host environment | Bootstrap uv, select install prefix/system-runtime compatibility and lifecycle; no full transitive lock required by this scope |
| Environment composition | Native aqua tags export the selected executable set; common Python requirements in this probe | Invoke the right selections/backends and define any additional real Python subsets |
| Host execution semantics | Explicit aqua config and uv no-project/no-config route preserve cwd without an own restore wrapper | Public release retrieval/lookup, dispatch, unsupported-command policy and compatibility surface |
| Container exposure | Direct native executable plus fixed venv works under non-root/network-denied conditions | Integrate build steps, permissions, PATH and relevant existing feature lifecycle |
| Portable Bazel compatibility | Reuse first-round real Ruff bridge proof | Bounded archive-layout mapping, generic registration/update checks where justified, Python metadata export; no complex packaging |
| Retention/security guarantees | Native checksum enforcement; direct prepared runtime needs no downloads | Artifact retention and release-grade provenance/offline acceptance, independent of manager choice |

Compared with mise, aqua does not provide one combined `install`/`bin-paths` API
for Python and native tools. The tested replacement is a small explicit
build/export plus uv-preparation sequence using native backend inputs; no generic
orchestrator was necessary. Conversely, mise already orders declared uv before
its Python backend and composes native config environments. These are real
workflow conveniences, but they do not themselves prove either architecture has
lower long-term maintenance. Both still need release/bootstrap, final image and
Bazel delivery integration. There is no demonstrated one-manager winner here.

## Remaining evidence and peer review

**Tested:** C1/C2/C3 outcomes above; first-round native Bazel bridge remains
valid. **Source-derived:** macOS ARM support from artifacts/resolution, not Mac
execution. **Untested:** actual macOS/ARM execution, complete catalog migration,
full Python-Bazel adapter, complete public Git-package UX, production image and
long-term archival. **Not required:** packaging complex tools for Bazel, identical
transitive environments, one universal config schema. **Blocked:** none of the
three agreed outcome checks.

Both peers have now read this report and challenged its maintenance/host/runtime
claims. Their feedback found no inconsistent capability or maintenance-overhead
claim. I read both complete round-two reports and the relevant mise release/run
scripts, Nix consumer/runtime scripts and update evidence:

- **mise:** changed-host and targeted changed-runtime versions are distinguished
  from the baseline full runtime fixture. Its tested `-C` route needs its small
  cwd-restore adapter; the report does not falsely claim a native alternative is
  impossible. Runtime install paths and system-Python venv are equivalent to the
  aqua prepared-runtime requirement. The revised costs matrix makes no unsupported
  total-maintenance saving claim.
- **Nix:** the independently changed second-input package selection reaches both
  its uv host export and the full C3 closure. Native host Nix remains honestly
  untested. Complete closure handoff succeeds under the same Ubuntu/user/network
  conditions; it is not a portability failure. A successful rather than failing
  pre-commit hook is a narrower evidence item, not a reason to invent another
  candidate capability gap or rerun the comparison.

All agents agree that no additional cases are needed for this comparison. The
remaining judgment is which demonstrated responsibilities the maintainers prefer
to own, plus the still-open consumer bootstrap/uv interface choice.
