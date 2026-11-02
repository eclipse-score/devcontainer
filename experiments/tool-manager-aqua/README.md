<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# aqua: bounded tool-management experiment

Local evaluation, 2026-10-30. No production sources changed, no container built,
no push/publication. This worktree contains the same decision-record snapshot as
the other candidates. Results below come from Linux x86_64; macOS ARM is a
source/metadata/resolution check, not an executed platform test.

## Verdict

aqua is a credible small native-CLI backend. Its registry takes ownership of
artifact naming, download/extraction recipes and platform differences; `aqua cp`
can provision direct image executables without a runtime manager. A separate
standard Python requirements file and uv satisfy the tested pre-commit use case.
That is two native configurations in one folder, which the requirements allow.

It is not a universal Python/environment manager. Choosing it means accepting
uv as a companion and owning the small integration between both backends and
existing delivery interfaces. Preserving `rules_multitool` needs a metadata
bridge: this probe proves Ruff, not a generic exporter for the complete catalog.
Do not add complex tools to Bazel merely to extend coverage.

## Authoring and generated files

| File | Ownership |
| --- | --- |
| [aqua.yaml](aqua.yaml) | Maintained direct native package pins, registry pin and environment tags; Ruff 0.11.13 and uv 0.11.2 |
| [requirements.txt](requirements.txt) | Maintained Python direct dependency: pre-commit 4.7.0; no handwritten transitive package list |
| [aqua-checksums.json](aqua-checksums.json) | Generated artifact/registry hashes for Linux amd64/arm64 and macOS ARM |
| [export_ruff_multitool.py](export_ruff_multitool.py) | 56-line Ruff-specific bridge experiment, including comments; reads aqua's resolved version and checksum output |
| [smoke.sh](smoke.sh) | Repeatable startability/exit-code smoke procedure; experiment harness, not product code |

uv 0.11.2 was selected deliberately to match the available known-working uv
version and minimize unrelated bootstrap variation. It is not a registry
limitation and not a recommendation to replace the repository's 0.13.6 pin.
The comparison's requested Ruff/pre-commit versions match the baseline exactly.

## Commands and observed results

The test bootstrap downloaded aqua **2.65.2** into
`/tmp/score-aqua-eval/bootstrap` using `gh release download`. The archive SHA256
matched the release checksum list:
`971abaccd16d0521fdb8e45990dba2aea17587f476aa075b621aeb972f52a61f`.
Release checksums were compared; bootstrap signature verification was not tested.
No global installation or configuration was changed. Generated/cache files live
under `/tmp/score-aqua-eval`; experiment metadata is in this folder.

From this worktree root, the reproducible basic probe is:

```sh
export AQUA_BINARY=/tmp/score-aqua-eval/bootstrap/aqua
export AQUA_ROOT_DIR=/tmp/score-aqua-eval/root
"$AQUA_BINARY" -c experiments/tool-manager-aqua/aqua.yaml update-checksum
PROBE_STATE_DIR=/tmp/score-aqua-eval/replay experiments/tool-manager-aqua/smoke.sh
```

Individual operations actually exercised:

| Operation | Observed result |
| --- | --- |
| `aqua -c aqua.yaml update-checksum` | Generated registry + artifact SHA256 entries for all three configured target platforms |
| `aqua -c aqua.yaml cp --tags container -o /tmp/score-aqua-eval/bin` | Direct Ruff, uv and uvx executables exported; no runtime aqua proxy needed |
| Exported `ruff --version` | `ruff 0.11.13` |
| `ruff check --isolated fixture.py` with `import os` | F401, exit **1** |
| `uv run --no-project --no-config --isolated --with-requirements requirements.txt pre-commit --version` | `pre-commit 4.7.0`; uv prepared 11 packages from the one direct requirement |
| Same command running `pre-commit run --all-files` in a temporary Git repository | Local `language: system` success hook passed, exit **0**, no hook environment downloads |
| Same version command with `UV_OFFLINE=true` after preparation | `pre-commit 4.7.0`; demonstrates this prepared cache, not a universal air-gap guarantee |
| `uv venv /tmp/score-aqua-eval/image-venv`, then `uv pip install --python .../bin/python -r requirements.txt` | Preinstalled direct `.../bin/pre-commit --version` prints 4.7.0; interpreter was CPython 3.14.3 |
| `uv pip compile --python-platform aarch64-apple-darwin requirements.txt` | Python dependency resolution succeeded for macOS ARM; no binaries executed on macOS |

The official Ruff registry recipe maps Linux to musl artifacts. This differs
from the old catalog's Linux GNU build but preserves the requested tool version;
our confirmed requirements allow platform-specific artifacts.

## Ordinary maintenance and selections

A separate temporary copy under `/tmp/score-aqua-eval/update` demonstrated:

```sh
aqua -c aqua.yaml update ruff@0.11.12
aqua -c aqua.yaml update-checksum --prune
aqua -c aqua.yaml cp --tags lint -o /tmp/score-aqua-eval/updated-bin
```

That output contains only Ruff and reports **0.11.12**. Only the native pin was
edited by aqua; checksums were regenerated. The Python temporary requirements pin
was changed to **4.5.1** and the same uv command reported pre-commit **4.5.1**.
Both directions prove that the backend definitions, rather than the host PATH,
select the tool version. The checked-in experiment retains 0.11.13 / 4.7.0.

`aqua generate rhysd/actionlint@v1.7.7` produced the package declaration from the
registry; maintainers can append it with `-i` and attach environment tags in that
one entry. Removal means deleting that declaration or environment tag and
rebuilding a fresh image/output directory, then pruning generated checksums.
Existing copied binaries are not uninstalled by removing a YAML entry. Likewise
`aqua remove` removes cache installations, **not** the declaration itself.

Tags supply native selection without repeated pins. A subtlety matters:
`aqua install --tags ...` still creates proxies for all declared tools and lazy
installation can fetch the others later. Use `aqua cp --tags ...` for the
container's fixed executable selection; tag-filtered install alone is not a
strict availability boundary. The Python probe uses the common requirements
selection; separate requirements files can use standard `-r` includes if a real
second Python environment needs a different subset. No invented profiles were
added merely to expand the prototype.

## Existing Bazel delivery: real but bounded bridge proof

The exporter resolves `aqua which --version ruff`, reads generated checksum IDs,
and derives the Ruff GitHub asset URLs and archive paths for the selected
release. It writes normal `rules_multitool` metadata with three platform entries;
it does not own another Ruff version pin.

```sh
AQUA_BINARY=/tmp/score-aqua-eval/bootstrap/aqua \
AQUA_ROOT_DIR=/tmp/score-aqua-eval/root \
python3 experiments/tool-manager-aqua/export_ruff_multitool.py > /tmp/score-aqua-eval/ruff.lock.json
```

A separate minimal workspace at `/tmp/score-aqua-eval/bazel` exports this generated
file, registers it via `rules_multitool` **1.11.1**, and uses Bazel **8.6.0**.
From that workspace:

```sh
bazelisk --output_base=/tmp/score-aqua-eval/bridge-output run \
  --lockfile_mode=off @multitool//tools/ruff:cwd -- --version
```

Result: **ruff 0.11.13**, successful Bazel build and execution. Consumer-side
native delivery did not invoke aqua or require host Python. The **generator**
requires Python, which is a maintainer prerequisite, not a Bazel user's one.

The 56 lines encode Ruff-specific tarball naming and extraction layout. Other
archive layouts, non-GitHub providers, aliases and auxiliary files need additional
mapping or an upstream supported export API. Existing Python Bazel targets can
retain a pinned uv runtime, but their metadata must derive from the requirements
owner; that adapter was inspected, not reimplemented or executed with this new
requirements file. Therefore this is **not** proof that a complete Bazel bridge
is already available for either native or Python catalogs.

## Container, host and #189 implications

- **Container:** build-stage aqua `cp` installs selected native binaries. Use the
  same requirements file to preinstall Python tools into an image-owned fixed
  environment; expose executables to the non-root user. The fixed-venv command
  was exercised locally, not in an actual image or as a non-root container user.
  Runtime ABI, chosen install prefix and venv paths must be correct in the image.
- **Host:** aqua can run configured native tools; pre-commit uses uv and the
  requirements file. Linux was tested; aqua/uv release artifacts and the generated
  Ruff/uv hashes cover macOS ARM. Linux ARM artifacts were resolved, not executed.
- **#189:** a consumer with only uv can use a requirements file from a selected
  release checkout and the tested `uv run --with-requirements` command. To provide
  the exact Git-release `uvx ... score-tool` UX without a checkout, a thin package
  must ship/read those requirements, or invoke another compatible packaged entry.
  That packaging/integration remains extra work; aqua does not supply it.
- **uv choice:** it is a natural companion because aqua has no PyPI backend. If uv
  remains the desired consumer bootstrap, no aqua installation is needed for the
  Python-only workflow. If a single manager must run Python tools itself, aqua
  leaves that requirement to another backend rather than meeting it alone.
- **run-tool:** keep trusting container-installed versions in both modes; strict
  host execution must select known configured tools. Do not assume aqua's generic
  command lookup is a strict allowlist: `aqua which` can fall back to PATH for an
  unconfigured command. Existing Bazel fallback or explicit registered selection
  can preserve the required strict boundary.

## Security, availability and remaining cost

Native checksum enforcement is explicitly enabled; it is not aqua's default.
Generated checksum entries are output artifacts and should be committed alongside
the native config. Registry recipes handle verification helpers: the tested uv
install additionally bootstrapped `gh` 2.102.0 for GitHub artifact attestation.
That was build-time behavior, not a direct dependency authored in our config.
Retaining artifact hashes does not by itself archive artifacts for ten years.

Python requirements pin the direct tool, not its transitive dependencies or the
interpreter. That meets the confirmed version-alignment scope. Prepared offline
execution passed for this probe; long-term archival, complete isolated offline
runs and downstream hook environments need their own evidence.

No production-wide migration, full Bazel Python adapter, non-root container build,
Mac execution or full tool coverage audit was attempted. Those gaps should be
weighed against the candidate's narrow scope, not filled with a custom framework.
The remaining own code is provisioning/orchestration, selected-release Python
packaging if required, and bounded Bazel metadata export. aqua eliminates native
artifact recipe ownership for registry-covered tools; it does not eliminate all
delivery integration.

## Primary sources and activity

- [aqua configuration](https://aquaproj.github.io/docs/reference/config/): registry pins, package entries and imports.
- [Registry package types](https://aquaproj.github.io/docs/reference/registry-config/): no native PyPI/Python package backend among the documented types.
- [Checksum configuration](https://aquaproj.github.io/docs/reference/config/checksum/): enforcement and generated checksum lifecycle.
- [Tag filtering](https://aquaproj.github.io/docs/guides/package-tag/): lazy-install caveat.
- [Container build guide](https://aquaproj.github.io/docs/guides/build-container-image/): binary copying and limitation to executable-only exports.
- [Ruff registry recipe](https://github.com/aquaproj/aqua-registry/blob/v4.579.0/pkgs/astral-sh/ruff/registry.yaml) and [uv recipe](https://github.com/aquaproj/aqua-registry/blob/v4.579.0/pkgs/astral-sh/uv/registry.yaml).
- [uv tools](https://docs.astral.sh/uv/guides/tools/) and the tested uv 0.11.2 CLI help distinguish tool execution and required environments.

GitHub API read on 2026-10-30: aqua has **1,878 stars**, registry **394**; both
repositories had pushes that day and neither was archived. This shows an active,
smaller ecosystem; stars are not a count of users or evidence of suitability.
