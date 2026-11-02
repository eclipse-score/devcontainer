<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Maintained mise reference: three tools, two selections

This is a bounded reusable reference, not a production migration or a candidate
selection. It implements the same checkpoint as the aqua/Nix references.

**Both releases passed:** Ruff 0.11.13 → 0.11.12, pre-commit 4.7.0 and
ShellCheck 0.10.0 unchanged. Each release provides a real normal uv dependency,
uvx invocation, three working Bazel CLI targets and prepared non-root/offline
Ubuntu runtimes for both selections. No publishing or global installation.

## Authoritative inputs

| Maintained file | Decision owned |
| --- | --- |
| `mise.native.toml` | Ruff direct version; shared by both selections |
| `mise.python.toml` | pre-commit direct version; shared by both selections |
| `mise.published.toml` | ShellCheck direct version and published-only membership |
| `mise.toml` | Empty common root, preventing implicit parent config selection |
| `provision.py` | Native environment composition: repository = native/python, published adds published env |
| Existing baseline `tools/lockfiles/uv.lock.json` | **Single helper uv version/platform-hash owner**; copied into the release and used to generate its mise uv declaration |

`mise.native.lock` is generated native resolution data, not another Ruff
version decision. `prepare.py` refreshes native Ruff/ShellCheck locks for exactly
Linux x64, Linux ARM64 and macOS ARM64. Python full-graph locking is not required;
locking only native env files avoids mise's optional Python graph/managed-runtime
requirements. Supported CLI versions, rather than identical binary/transitive
artifacts, are the common contract.

The update [authoritative diff](evidence/authoritative.diff) changes exactly one
Ruff TOML line. [Generated diff](evidence/generated.diff) shows the resulting
native lock, portable Bazel metadata and Python dependency change. Generated
Python metadata/uv.lock pins are outputs, not separately edited authorities.

## Prepare and consume

Producer prerequisites are Linux x64, Python 3.12+, Git, curl/sha256sum and online
artifact access. Docker is needed for the shared runtime checks, Bazel and uv/uvx
for their corresponding consumer checks. Bootstrap is explicitly isolated:

```sh
bash experiments/tool-manager-mise/reference/bootstrap.sh /tmp/score-mise-reference-bootstrap
export MISE_BINARY=/tmp/score-mise-reference-bootstrap/mise
export SCORE_MISE_REFERENCE_STATE=/tmp/score-mise-reference-tools
python3 experiments/tool-manager-mise/reference/prepare.py /tmp/mise-release --version 0.1.0
```

The bootstrap pins verified mise 2026.10.24 with SHA256. This reference does not
supply a macOS bootstrap; ARM Mac coverage is artifact metadata, not execution.
The captured run reused the earlier private verified mise binary and the
`/tmp/score-mise-evaluation-fresh` installation state, whose pre-commit venv uses
system Python 3.12.3. No inherited global manager/settings are required. A new
state can install through the same native provisioner; a second clean-state
bootstrap was not redundantly benchmarked here.

The fresh release directory contains:

- Native configs/locks, isolated bootstrap and `provision.py`; it can reprovision
  definitions without the original checkout and with explicit `MISE_BINARY`.
- `native/`: complete installed Ruff/ShellCheck/pre-commit trees, preserving venv
  symlinks and canonical absolute installation prefixes. This is a runtime
  snapshot, not a lease on the producer cache.
- Generated `profiles/{published,repository}.sh` and `*.runtime.json`, derived
  from **active native mise selections**, including executable paths/versions.
- `install.sh`: copies only the selected full trees into an image root and
  exposes its commands; neither mise nor a Python metadata parser is needed
  during this image assembly.
- Standard static setuptools `pyproject.toml`, no module or custom entrypoint,
  with `ruff` and `pre-commit` extras generated from their native owners.
- `MODULE.bazel`, `.bazelversion` and public `//tools:{ruff,shellcheck,pre-commit}`
  targets with generated native locks and Python metadata.

```sh
bash /tmp/mise-release/install.sh /tmp/mise-image-root published
# Standard package release artifact; illustrative name/API, no publication:
uv build --wheel --out-dir /tmp/mise-release/dist /tmp/mise-release
uv add --raw 'score-mise-reference[ruff,pre-commit] @ file:///ABS/score_mise_reference-0.1.0-py3-none-any.whl'
uv run --locked ruff --version
uv run --locked pre-commit --version
uvx --with 'score-mise-reference[ruff,pre-commit] @ file:///ABS/score_mise_reference-0.1.0-py3-none-any.whl' ruff --version
# Same standard form with pre-commit as the final executable also works.
```

Consumer selects only the release/extra, never another Ruff/pre-commit pin. uvx
`--with` uses the facade's dependency in the same resolver; it runs the real
upstream CLI without the earlier dependency-executable warning. ShellCheck has
native/Bazel delivery; no artificial Python wrapper was added.

## Reproduce the shared acceptance check

```sh
export MISE_BINARY=/absolute/isolated/mise
python3 experiments/tool-manager-mise/reference/check.py --state /tmp/new-mise-reference-check
```

Use a fresh state path. `check.py` prepares a baseline, changes Ruff in an isolated
copy of the same native input and repeats the same prepare/consumer path. It
captures exact argv, cwd, stdout/stderr and statuses; no separate updated
implementation is maintained. Output wheels and large runtime snapshots remain
under the chosen `/tmp` state, while bounded captured evidence lives here.

| Check | Observed result |
| --- | --- |
| Standard wheel build + installed `Requires-Dist` | Exact selected Ruff/pre-commit dependencies in both releases |
| Ordinary uv project + uv.lock + real Ruff/pre-commit | Ruff .13 then .12; pre-commit 4.7.0; F401 exit 1 and local cwd/argument hook passes |
| Actual uvx `--with` for both Python CLIs | Exact expected versions, no custom runner or producer manager on consumer PATH |
| Real Bazel targets for all three | Exact selected versions; Ruff F401 exit 1, ShellCheck SC2086 exit 1, real pre-commit cwd/argument hook passes |
| Published prepared Ubuntu | Both releases: uid12345/network none, all three exact versions and functional shared fixtures pass |
| Repository prepared Ubuntu | Both releases: Ruff/pre-commit functional checks pass; ShellCheck absent from PATH |
| Update consistency | Ruff-only authoring change; ShellCheck/pre-commit definitions and helper artifact metadata remain byte-identical |

[evidence/commands.json](evidence/commands.json) records the 46 consumer/assembly/
runtime commands. The unchanged parent-provided `runtime-check.sh` is used for
all four profile/release runtime checks. Each runs the common Ubuntu image with
`--network=none`, selected assembled trees mounted read-only, a writable tmp/home,
and no mise/aqua/Nix/uv/uvx on PATH. Runtime mounts come from release image assembly,
**not** the producer's original installation directory.

A separate targeted [managed-Python proof](evidence/managed-python-bazel.json)
invoked actual Bazel pre-commit with `UV_PYTHON_PREFERENCE=only-managed`, automatic
Python downloads and isolated cache/install directories. It downloaded CPython
3.15.2 and executed pre-commit 4.7.0 successfully. Thus the Bazel route can bootstrap
Python rather than introducing host Python as a consumer prerequisite. PyYAML
6.0.3 was built from source in that run; a compiler-free first bootstrap is
therefore not established or promised. The
maintained checker uses these same isolated settings for Bazel calls. The full
46-command capture used the default uv Python preference; do not relabel it as
46 clean managed-Python bootstraps. First-use Bazel may require network; this
reference promises prepared-container offline execution, not offline cold uvx.

## Integration ledger

| Permanent integration responsibility | Supplied upstream or reused | What remains ours |
| --- | --- | --- |
| Version and environment ownership | Native mise env config/install | Native/Python profile composition, tool decisions, supported-platform policy |
| Artifact resolution | mise aqua backend/native lock | Lock refresh convention and provenance/retention policy |
| Portable simple Bazel interface | Existing Multitool, shared baseline uv lock and unchanged Python/cwd shell adapters | Bounded Ruff/ShellCheck archive member/platform mapping, generated registrations and freshness checks |
| Python delivery | Standard setuptools metadata/build and uv resolver/executables | Applicable native/PyPI/extra name mapping and static dependency export |
| Runtime handoff | mise creates selected install trees/venvs | Preserve complete absolute prefixes, compatible base Python/ABI, selected exposure and image assembly |
| Release production | Standard wheel/build and immutable source/artifact mechanisms | Bind configs, locks, Bazel metadata and package metadata to the same release; prevent stale output |
| Verification | Shared external runtime script, real CLI fixtures | Keep prepare/check and integration assertions meaningful |

`prepare.py`, `provision.py`, `install.sh` and the bounded generators are reusable
reference integration. `check.py`, isolated before/after source copies, consumer
fixtures and command evidence are verification. Temporary outputs/LOC are not
production abstractions or complexity scores. The shared runtime script and
baseline Bazel adapters are copied unchanged, not independently redesigned.

This is real integration for **these three tools and two profiles**. It does not
claim full S-CORE/feature migration, complete catalog mappings, complex Bazel tool
packaging, offline cold package resolution, public release retrieval/retention,
or actual Mac execution. Canonical `/tmp/...` prefixes are explicit reference
choices; a production prefix/base-runtime policy remains to be decided.

## Peer review

Read both final aqua/Nix reference reports and their prepare/install code, and
exchanged concrete feedback:
aqua's native tags/Python dependency groups and fixed target-ABI venv are valid
owners; Nix's profile selectors and complete closure handoff are valid owners.
Both reuse the same baseline Bazel helper and ordinary static dependency model.
Nix's portable binary digests remain separate from Nix source hashes. No concrete
scope/ownership objection was found. Peers read this reference's sources and
confirmed the native owner/generated metadata/runtime boundaries; their useful
managed-Python bootstrap check was adopted directly.

All three implementations are being continued equally. This checkpoint measures
actual integration responsibilities; it does not choose a manager or establish
whole-migration maintenance hours.

Maintained-source pre-commit passed (Ruff format/check, ShellCheck, copyright,
REUSE, executable/shebang and text checks). Only the unrelated global
`bzlmod-tidy`/`bzlmod-lockfile` hooks were explicitly skipped because production
modules were unchanged; generated reference modules were actually run above.
See [source check log](evidence/source-precommit.log).
