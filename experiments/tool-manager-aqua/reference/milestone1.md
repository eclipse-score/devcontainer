<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Aqua reference: two selections and three delivery paths

Historical report: the current producer has progressed to milestone 2. Commands
and absent-tool expectations below describe the captured milestone-one state;
see README.md for current reproduction.

This maintained reference reaches the shared milestone for Ruff, ShellCheck and
pre-commit. No manager or public package API is selected. It replaces additional
single-tool probes with one producer and one acceptance entrypoint.

| Delivery | Baseline release 0.1.1 | Updated release 0.2.0 |
| --- | --- | --- |
| Native `published` | Ruff 0.11.13, ShellCheck 0.10.0, pre-commit 4.7.0 | Ruff 0.11.12; other versions unchanged |
| Native `repository` | Ruff 0.11.13, pre-commit 4.7.0; no ShellCheck | Ruff 0.11.12; pre-commit unchanged; no ShellCheck |
| Prepared Ubuntu, both selections | Shared external check passed, uid 12345, network denied | Same check passed for both updated selections |
| Bazel public CLI targets | All three actually executed, including behavior fixtures | All three actually executed, including behavior fixtures |
| Standard uv project and uvx | Both Python CLIs actually executed for both extras | Both Python CLIs resolve and execute updated release |

Versions are deliberate existing update fixtures, not proposed downgrades. The
same `prepare.py` and `check.py` paths produced/tested both releases. The version
change was made with native `aqua update`, not by editing generated Python or
Bazel metadata. ShellCheck is deliberately absent from Python delivery.

## Authored sources and generated outputs

- [aqua.yaml](aqua.yaml) owns native Ruff/ShellCheck versions and their environment
  tags. Registry v4.579.0 owns download recipes. Checksum enforcement is enabled.
- [pyproject.toml](pyproject.toml) owns the pre-commit direct pin in ordinary uv
  dependency groups. `published` includes `repository`, so the Python selection
  is not repeated. These groups describe this backend's membership; native tags
  describe the native backend's membership. No custom universal schema is used.
- [aqua-checksums.json](aqua-checksums.json) is generated native artifact data.
- [prepare.py](prepare.py) snapshots the owners, refreshes native checksums,
  derives selections, copies selected native binaries with `aqua cp`, prepares
  both fixed Python environments against actual Ubuntu, builds the standard
  facade wheel and writes the small Bazel module.
- [provision.sh](provision.sh) is the release's reusable initial installer. It
  needs aqua/uv only during provisioning. It exposes console scripts discovered
  from the selected direct Python distributions; no separate pre-commit pin or
  membership list is maintained in shell.
- [check.py](check.py) verifies outputs. [runtime-check.sh](runtime-check.sh) is
  the unchanged shared external acceptance script, copied from the primary
  comparison directory. Neither is production dispatch code.

A prepared release contains the authoritative snapshots, generated checksums and
requirements, installer, `selection.json`, `package/pyproject.toml`, `dist/*.whl`,
`bazel/` and complete `runtime/{published,repository}` directories. The installer
and its inputs work without the original checkout. The producer itself remains
in this source tree because it deliberately reuses the existing baseline Bazel
adapters and uv helper rather than vendoring independent copies into authoring.

The generated package `score-aqua-reference` has no application module, custom
installer or console entrypoint. Standard setuptools metadata exposes `ruff`,
`pre-commit`, `published` and `repository` extras. Ruff's pin derives from aqua;
pre-commit's pin derives from the dependency group. Normal `Requires-Dist` makes
both visible to uv's resolver. Package name/extra/release numbering are local
reference choices, not an adopted API. Consumer projects select our release;
they do not author another upstream tool pin.

## Reproduce

Producer prerequisites: Linux x86_64, Python 3.11+ with PyYAML, aqua, uv/uvx,
Docker with the shared Ubuntu base, and Bazel 8.6.0. The generator uses Python;
the generated Bazel CLI consumer adds no host Python prerequisite. Tested aqua
is 2.65.2, producer/consumer uv is 0.11.2, Docker runtime Python is 3.12.3. This
continues the earlier isolated bootstrap, without global manager installations.
The Bazel uv helper independently uses the existing baseline artifact lock's
0.13.6. That baseline file remains its only maintained version/hash owner.

From this worktree root, with those isolated executables already available:

```sh
export AQUA_BINARY=/tmp/score-aqua-eval/bootstrap/aqua
export UV_BINARY=/tmp/score-aqua-eval/bin/uv
export AQUA_ROOT_DIR=/tmp/score-aqua-eval/root
export UV_CACHE_DIR=/tmp/score-aqua-reference/uv-cache
python3 experiments/tool-manager-aqua/reference/prepare.py \
  /tmp/score-aqua-reference/releases/0.1.1 --version 0.1.1
python3 experiments/tool-manager-aqua/reference/check.py \
  /tmp/score-aqua-reference/releases/0.1.1 \
  /tmp/score-aqua-reference/evidence/0.1.1
```

Use fresh output/evidence directories when repeating. The producer refreshes
checksums only in the release snapshot. After an intended central update, retain
its generated checksums alongside the authored source, as done for the baseline
in this directory. Bootstrap aqua came from its v2.65.2 Linux AMD64 release archive
via `gh release download`; its SHA256 was compared with upstream checksums:
`971abaccd16d0521fdb8e45990dba2aea17587f476aa075b621aeb972f52a61f`.
Bootstrap signature verification is not claimed. An existing uv/Python producer
can be replaced with an isolated local installation; no consumer needs aqua.

The generated Bazel module exposes:

```sh
cd /tmp/score-aqua-reference/releases/0.1.1/bazel
bazel --output_base=/tmp/score-aqua-reference/bazel-output run //tools:ruff -- --version
bazel --output_base=/tmp/score-aqua-reference/bazel-output run //tools:shellcheck -- --version
bazel --output_base=/tmp/score-aqua-reference/bazel-output run //tools:pre-commit -- --version
```

The standard package can be consumed directly, without producer managers:

```sh
uv add --raw 'score-aqua-reference[published] @ file:///tmp/score-aqua-reference/releases/0.1.1/dist/score_aqua_reference-0.1.1-py3-none-any.whl'
uv run --locked ruff --version
uv run --locked pre-commit --version
uvx --with 'score-aqua-reference[repository] @ file:///tmp/score-aqua-reference/releases/0.1.1/dist/score_aqua_reference-0.1.1-py3-none-any.whl' pre-commit --version
```

`check.py` runs those workflows for both selections and both Python CLIs with
consumer PATH restricted to `/usr/bin:/bin`. `uvx --with` uses ordinary resolution
and emits no dependency-executable warning. It also records consumer locks and
runs the generated Bazel targets from a consumer subdirectory. Actual error
fixtures return 1 for Ruff F401 and ShellCheck SC2086; pre-commit's local system
hook checks caller cwd and an argument containing a space. Earlier hostile host
config/PATH selection evidence remains valid; a new runner UI is not introduced.

## Central update and evidence

The update used an isolated copy of the same native sources, preserving the
checked-in baseline. The actual commands were:

```sh
mkdir -p /tmp/score-aqua-reference/update-source
cp experiments/tool-manager-aqua/reference/aqua.yaml \
  experiments/tool-manager-aqua/reference/pyproject.toml \
  experiments/tool-manager-aqua/reference/aqua-checksums.json \
  /tmp/score-aqua-reference/update-source/
"$AQUA_BINARY" -c /tmp/score-aqua-reference/update-source/aqua.yaml update ruff@0.11.12
python3 experiments/tool-manager-aqua/reference/prepare.py \
  /tmp/score-aqua-reference/releases/0.2.0 --version 0.2.0 \
  --source /tmp/score-aqua-reference/update-source
python3 experiments/tool-manager-aqua/reference/check.py \
  /tmp/score-aqua-reference/releases/0.2.0 \
  /tmp/score-aqua-reference/evidence/0.2.0
```

The only authored tool change is
`astral-sh/ruff@0.11.13` → `astral-sh/ruff@0.11.12`.
The facade's separate release identifier changes to 0.2.0. Native hashes, Python
extras, Bazel artifact metadata and resolver locks follow automatically.

[evidence/](evidence/) retains the authored/generated diffs, both exact command
records and summaries, native selections, generated native locks/Python catalog,
wheel `METADATA`, consumer pyprojects and uv locks. Both full checks recorded 24
commands. Tool count is not a complexity score. The two other direct versions
were additionally compared between generated selections and remained unchanged.
Original prepared binaries/venvs/wheels remain under
`/tmp/score-aqua-reference/releases/{0.1.1,0.2.0}` rather than being committed.

A targeted additional Bazel pre-commit run used `UV_PYTHON_PREFERENCE=only-managed`,
`UV_PYTHON_DOWNLOADS=automatic`, isolated `UV_PYTHON_INSTALL_DIR` and a separate
Bazel uv cache. It downloaded CPython 3.15.2 into the candidate's `/tmp` prefix and
executed pre-commit 4.7.0. The earlier complete checks reused an already available
managed interpreter. The corrected `check.py` now isolates these paths itself.
This proves the lightweight adapter can provision its own interpreter; it does
not claim a compiler-free initial install: current resolution built PyYAML 6.0.3
from source in this targeted run. No runtime interpreter pin or new launcher was
invented to hide that behavior. See [managed-python evidence](evidence/managed-python.json).

## Runtime and Bazel boundaries

Both runtime selections were exercised in
`score-tool-manager-comparison-base:20261031`, image ID
`sha256:1b1ebf493ffb1a5a3a4d3c4c2a822cfe0da563d7028159078b0a02a12122a28d`,
with `--network none`, uid/gid 12345, a readonly prepared prefix and writable
home/tmp. The shared check verifies all expected versions, absent managers/uv,
ShellCheck exclusion, real analysis errors and the local pre-commit hook.

The complete chosen runtime is mounted at `/opt/score-tools`. Its Python venv
must stay at that absolute path and requires compatible system Python/Git.
Native binaries execute directly. No aqua shim, uv, network package resolver or
runtime installation participates in container execution. Both run-tool modes
trust those prepared tools, as specified in the decision record.

Bazel reuses the baseline `python_tool.bzl`, `multitool.bzl`,
`internal/run_python_tool.sh` and `uv.lock.json` unchanged. Ruff/ShellCheck
portable metadata derives from aqua's generated checksums; explicit exact
artifact allowlists cover Linux AMD64/ARM64 and macOS ARM64. Ruff uses musl release
binaries. Archive member/layout and backend→distribution identities remain owned
by the bounded adapter. No source hash is substituted for an archive hash.

The lightweight Python Bazel launcher initially resolves/downloads dependencies
through its pinned uvx helper. That established route is not an offline/archival
solution; no new claim of fully predeclared Bazel action inputs is made. The
network-denied prepared container runtime is a distinct tested delivery path.
macOS ARM/Linux ARM artifact metadata is generated; actual execution here was
Linux AMD64 only. Production image/features, complex tools, release publication,
retention and complete downstream migration remain outside this milestone.

## Permanent maintenance ledger

| Responsibility | Upstream/backend handles | We retain |
| --- | --- | --- |
| Native tool definition | aqua registry recipes and checksum extraction | Direct versions, native environment tags and registry refresh |
| Python selection | Standard uv groups and package resolution | Direct pre-commit dependency/group inheritance |
| Initial provisioning | aqua binary copying; uv venv/install | Sequence, fixed prefix/ABI, executable exposure and release snapshots |
| uv consumer interface | Standard setuptools/Requires-Dist and uv resolver | Bounded native/PyPI identity mapping, generated extras, package build/release |
| Bazel native delivery | Multitool fetch/extract/platform runtime | Known archive-layout/platform mapping and generated registrations |
| Bazel Python delivery | Existing pinned uvx + baseline shell adapter | Generate selected direct metadata; initial-fetch/runtime policy |
| Release correctness | Native checksums and ordinary resolver locks | Regenerate outputs, drift checks, bind image/package/Bazel outputs to release |
| Runtime validation | Shared external acceptance semantics | Two prepared non-root runtimes, ABI and complete prefix retention |

Temporary update directories, disposable uv projects, logs and evidence copies
are acceptance fixtures. They are not additional production catalogs or a
publishing framework. Generated output volume and elapsed test time do not
measure maintenance effort. Aqua needs explicit aqua/uv orchestration; mise's
common frontend and Nix's package-set/closure model have their own maintained
conventions. The standard facade and bounded Bazel integration remain shared
classes of responsibility across all three.

## Peer review

Read the maintained mise and Nix reference producer, profile/owner definitions,
installer and check paths. Both reuse the same baseline lightweight Bazel adapter;
Nix preserves a complete store closure and separately resolves portable upstream
archive hashes, while mise provisions selected native/Python installs through its
frontend. Their standard package exports remove producer-manager prerequisites
from uv consumers just like this reference. No ownership/runtime contradiction
was found in the inspected code. Both agents reviewed this producer/check code;
Nix confirmed the native tags/Python-group split and fixed runtime prefix, and
adopted the isolated managed-Python acceptance clarification. Both peers subsequently read this final report and stored results and confirmed
there was no factual correction. Their final source/install/report paths were
reviewed in return, completing the mutual review without ranking by test counts.

Maintained-source pre-commit checks passed (YAML, formatting, Ruff, ShellCheck,
copyright and REUSE). The two repository-wide bzlmod mutation/check hooks were
explicitly skipped to keep production sources outside this reference change;
Bazel formatting used a candidate-isolated output base and lockfile error mode.
The shared runtime script remains byte-identical to the primary copy. See
[evidence/source-precommit.txt](evidence/source-precommit.txt).
