<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Local release and update workflow

The maintained Aqua owner selects native versions and profiles; Python dependency
groups select Python requirements. A release produces an ordinary dependency
wheel, not a manager executable or a native runtime bundle. Its `ruff` extra
comes from the native Ruff owner; Python extras come from the Python owner.
Consumers use normal uv commands without Aqua, producer source, or a SCORE runner.
Other native tools are delivered by provisioning or the existing Bazel targets.

Run maintainer commands from the repository root with Python 3.11+, PyYAML, uv,
and network access to the configured release/package sources. Aqua is bootstrapped
from the checked owner manifest unless `AQUA_BINARY` names an existing executable.
`AQUA_ROOT_DIR` and `UV_CACHE_DIR` may select reusable manager caches. Prepared
native tools execute directly; the managers are provisioning prerequisites.
Bazel compatibility checks additionally require the workspace Bazel version.

## Prepare and validate a release

First check the current generated files. After changing an exact native version
in `tools/owners/aqua/aqua.yaml` or a Python requirement in
`tools/owners/aqua/pyproject.toml`, refresh before checking again:

```sh
python3 tools/internal/aqua/refresh_owners.py
python3 tools/internal/aqua/sync_repository.py --check
python3 tools/internal/sync_readme.py --check
```

Refresh updates bootstrap hashes, Aqua checksums, portable Bazel lockfiles,
Python compatibility versions, repository selection, and the README table.
Do not edit a generated Ruff pin separately. Missing current artifact checksums
cause the check to fail before refresh. Review the diff: unrelated selections
and versions must stay unchanged. Supported artifact layouts are translated in
`export_native.py`; a new version with the same layout needs no new translation.

Build into an empty directory outside the checkout. Both distribution identity
and release version are explicit. These names and versions are local examples;
they do not select a public package identity or hosting service.

```sh
python3 tools/internal/aqua/prepare_dependency_release.py \
  --output /tmp/aqua-handoff/A --version 0.8.0 \
  --package-name score-aqua-local --uv /path/to/uv
python3 tools/internal/aqua/check_dependency_release.py \
  /tmp/aqua-handoff/A /tmp/aqua-check-A \
  --uv /path/to/uv --uvx /path/to/uvx
```

The manifest binds the wheel hash, name, release version, owner digest, and full
profile selections. The checker validates those bindings against the current
owners and runs a fresh ordinary uv/uvx repository-extra consumer. Its evidence
directory must be fresh; it is a release check, not a consumer update command.
Use `--owner-dir` for an explicitly preserved owner snapshot when checking an
older release. An A release must fail validation against changed B owners.

For B, edit only the intended owner version, run refresh/check, then repeat the
two release commands with version `0.8.1`, output `/tmp/aqua-handoff/B`, and fresh
check directory `/tmp/aqua-check-B`. Keep the same distribution name. Retain
`release.json`, `selection.json`, generated package metadata, and the wheel in
the handoff. Build isolation currently resolves `setuptools>=77`; the manifest
records produced bytes, not a claim of a locked reproducible build toolchain.

## Update an independent uv consumer

Put both handoff wheels in one local wheel directory:

```sh
mkdir -p /tmp/aqua-handoff/wheels
cp /tmp/aqua-handoff/A/dist/*.whl /tmp/aqua-handoff/wheels/
cp /tmp/aqua-handoff/B/dist/*.whl /tmp/aqua-handoff/wheels/
```

In an independent project, set the dependency to
`score-aqua-local[ruff]==0.8.0` in its `pyproject.toml`, then run:

```sh
uv lock --find-links /tmp/aqua-handoff/wheels
uv sync --locked
uv run --locked ruff --version
uvx --find-links /tmp/aqua-handoff/wheels \
  --with 'score-aqua-local[ruff]==0.8.0' ruff --version
```

Change only that release requirement to `score-aqua-local[ruff]==0.8.1` and repeat
lock/sync/run; use `0.8.1` in the ordinary uvx command as well. The wheel extra
supplies Ruff's exact version. Keep the resulting `uv.lock` in the consumer;
inspect `Requires-Dist` in the wheels to trace its owner-derived dependency.
`ruff check --isolated 'bad input.py'` on `import os` returns F401 and exit 1.
Warm caches permit `--offline` sync/run/uvx; a first resolution may need the
normal Python index. Neither consumer needs the producer manager or source.

## Reprovision the same native prefix

With A owners, provision once; after updating owners to B, run the same command
against the same user-owned prefix:

```sh
python3 tools/internal/devcontainer/provision_host_tools.py \
  --profile repository --prefix "$HOME/.local/share/score-tools"
export SCORE_TOOLS_BIN="$HOME/.local/share/score-tools/bin"
export PATH="$SCORE_TOOLS_BIN:$PATH"
ruff --version
tools/run-tool --strict ruff --version
```

The provisioner takes the intended current owners, not the dependency wheel.
An isolated source/owner snapshot can use `--owner-dir PATH`. It recopies selected
native commands and runs uv tool installation when the owner digest changes;
caches avoid redownloading unchanged artifacts. It preserves unrelated names,
protects foreign or user-replaced selected paths, and reconciles deselection.
Use a fresh prefix if no supported ownership ledger exists. Only selected Aqua
outputs are exposed; transitive manager dependencies remain private. Normal
prepared calls require no manager resolution or Bazel launch.

For explicit Bazel compatibility, after refresh execute the existing public
interface from the checkout (or a subdirectory for a cwd/relative-argument check):

```sh
bazel run //tools:ruff -- --version
bazel run //tools:ruff -- check --isolated 'bad input.py'
```

This separately checks generated artifact URL/hash/layout selection. It does
not make Bazel a dependency of ordinary uv or prepared native execution.

## Responsibility and retained APIs

| Frequency | Maintainer or user responsibility |
| --- | --- |
| One time | Establish Python/uv/Aqua cache prerequisites and a supported user prefix; select release identity and hosting separately when authorized. |
| Per tool version | Edit one owner request; refresh checksum/compatibility outputs; review unrelated selections and supported layouts; validate actual tool behavior. |
| Per release | Choose explicit package identity/version, build/check into fresh external directories, retain owner-bound manifests/wheels, verify the public Bazel contract. |
| Per platform | Verify registry/artifact/bootstrap coverage and portable layout adapter, then provision and execute that platform; a Linux amd64 release check does not establish ARM/macOS execution. |
| User update | Change facade release requirement, lock/sync the same project, or reprovision the same native prefix from current owners; keep consumer lockfiles. |

No maintained helper is removed: refresh obtains artifact authority; sync derives
and checks compatibility files; preparation builds the dependency artifact;
checking validates its identity and consumer behavior; provisioning maintains
the native prefix. These are distinct exercised boundaries. Historical reports
remain evidence. This document centralizes the release sequence without adding
an orchestration wrapper or a production dependency on experimental files.
