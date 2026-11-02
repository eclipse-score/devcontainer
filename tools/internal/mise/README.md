<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Update, release, and consume the mise tool selection

Versions live in `tools/mise/mise.native.toml`, `mise.published.toml`, and
`mise.python.toml`. Edit the appropriate owner once. Mise artifact locks,
Bazel compatibility definitions, Python compatibility versions, the inventory,
and ordinary dependency-wheel extras derive from those owners.

The commands below run from the repository root unless a consumer directory
is specified. No public package identity or release host is selected here.

## Maintainer: change a tool version

Owner refresh currently requires Linux x86_64, Python 3.11 or newer, curl,
network access to the selected release metadata, and the checksum-pinned mise
bootstrap. `refresh.sh` bootstraps mise temporarily; `MISE_BINARY` may point to
an existing copy installed by `bootstrap.sh`. No global installation is needed.

1. Change only the desired owner entry, for example the Ruff backend in
   `tools/mise/mise.native.toml`. Do not edit generated Bazel lockfiles or copy
   the Ruff version into a consumer project.
2. Before refresh, `python3 tools/internal/mise/refresh.py --check` rejects a
   changed owner whose artifact lock is stale. Resolve and export normally:

   ```sh
   tools/internal/mise/refresh.sh
   python3 tools/internal/mise/refresh.py --check
   python3 tools/internal/sync_readme.py --check
   ```

3. Review the owner diff and generated artifacts. A Ruff-only update should
   change its owner entry, its entries in `mise.native.lock`,
   `tools/lockfiles/ruff.lock.json`, and the generated inventory row. Unrelated
   selections and pins should stay unchanged. The updater retains the
   declared platform set and archive-layout mapping; adding a tool or platform
   can require a backend/entrypoint or artifact-layout adjustment and execution
   on that platform.
4. Run the checks affected by the change. For Ruff, the public compatibility
   interface remains:

   ```sh
   bazel run //tools:ruff -- --version
   bazel run //tools:ruff -- check path/to/input.py
   ```

   Arguments after `--` reach Ruff in the caller's working directory. A lint
   failure returns Ruff's nonzero status. Bazel is an explicit compatibility
   consumer here; ordinary prepared commands and uv consumers run directly.

An exact historical version still requires knowledge of its existence and
available release artifacts. Mise resolves metadata for the version requested;
it does not establish that an arbitrary requested version exists. The local
0.14.6 update was selected from prior experiment knowledge, then resolved
through the normal mise backend without a historical generator dependency.

## Maintainer: build a local ordinary dependency release

Compatible uv and Python are required. After the refresh checks pass, choose a
package name and a concrete PEP 440 release version explicitly. Keep artifacts
outside the source tree and use an empty output directory for each release:

```sh
release_root=/absolute/path/to/local-handoff
package_name=chosen-local-dependency-name
release_version=0.8.1
python3 tools/internal/mise/python_package.py build \
  --output "${release_root}/${release_version}" \
  --version "${release_version}" \
  --package-name "${package_name}"
python3 tools/internal/mise/python_package.py check \
  "${release_root}/${release_version}"
mkdir -p "${release_root}/wheels"
cp "${release_root}/${release_version}/dist/"*.whl "${release_root}/wheels/"
```

`--uv /absolute/path/to/uv` can select an existing compatible uv executable.
The wheel contains static dependency extras and no SCORE command entrypoint.
Its `Requires-Dist` records contain exact owner-derived package versions.
`release.json` binds the explicit package name/version, owner-file hashes,
Python policy, extras, selected versions, and wheel digest. The check rejects
an older release against changed owners; validate an archived release against
its matching owner snapshot. Do not edit its manifest to make it appear current.

Keep the checked wheel, manifest, source identity, and owner snapshot together
for handoff. Publishing, credentials, public naming, and hosting are separate
decisions. A dependency wheel delivers Python distributions; it does not install
native feature commands or supply a Python interpreter or uv to consumers.

## User: update an independent uv project

The consumer needs compatible uv, a supported Python, access to the wheel
handoff directory, and access to its dependencies through PyPI or a prepared
cache. It needs no mise, Bazel, producer source tree, or SCORE runner.

For example, if the chosen facade name is `chosen-local-dependency-name`, the
project dependency is:

```toml
[project]
name = "independent-tool-consumer"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["chosen-local-dependency-name[ruff]==0.8.0"]
```

In that same project directory, lock, sync, and run normally:

```sh
wheelhouse=/absolute/path/to/local-handoff/wheels
uv lock --find-links "${wheelhouse}"
uv sync --locked --find-links "${wheelhouse}"
uv run --no-sync ruff --version
uv run --no-sync ruff check 'path with spaces/input.py'
```

To update, change only the facade requirement from `==0.8.0` to `==0.8.1`,
then repeat lock/sync/run in the same project. Retain `uv.lock` in the consumer
project: it records the resolved facade and Ruff versions. Do not add a second
Ruff pin. Select other supported extras, such as `pre-commit`, when needed.

For an isolated ordinary uvx invocation, select the same facade release:

```sh
uvx --find-links "${wheelhouse}" \
  --from 'chosen-local-dependency-name[ruff]==0.8.1' ruff --version
uvx --find-links "${wheelhouse}" \
  --from 'chosen-local-dependency-name[ruff]==0.8.1' ruff check input.py
```

uvx may advise that Ruff's executable is supplied by the selected dependency
extra; the command still resolves and executes the facade's pinned dependency.
Offline use requires cached dependency wheels and index metadata as well as the
local facade wheel.

## User: update a prepared native environment

Use the updated owner/config snapshot and reprovision the same selected
environment into the same user-owned prefix. For a repository selection:

```sh
bash tools/internal/mise/bootstrap.sh "${HOME}/.cache/score-tools/mise"
python3 tools/internal/mise/provision.py repository \
  --data-dir "${HOME}/.local/share/score-tools/mise-data" \
  --bin-dir "${HOME}/.local/share/score-tools/bin" \
  --mise "${HOME}/.cache/score-tools/mise/mise"
export PATH="${HOME}/.local/share/score-tools/bin:${PATH}"
ruff --version
ruff check input.py
```

Reuse that data directory and bin directory on subsequent updates. Initial
setup requires an untracked selected-command path to be absent. Provisioning
replaces its recorded Ruff link, preserves other selected commands and unrelated
user files, and protects commands selected by another environment. Conflicting
same-name selections at different versions are reported rather than overwritten.
No manager or Bazel invocation occurs for a prepared direct call. Optional
strict host verification uses the existing interface:

```sh
RUN_TOOL_CONTAINER_MODE=host \
SCORE_TOOLS_BIN_DIR="${HOME}/.local/share/score-tools/bin" \
  tools/run-tool --strict ruff --version
```

The native-prefix update and Python facade release are separate deliveries
derived from the same owners. Installing a new facade does not mutate a native
prefix; reprovisioning a native prefix does not update a consumer's uv lock.

## Maintenance responsibilities and retained interfaces

| Cadence | Work |
| --- | --- |
| One-time source repair | Keep stale-lock rejection active even under optimized Python; regression coverage checks normal and optimized execution. |
| Each version update | Edit the single owner, resolve locks/export compatibility metadata and inventory, review unrelated pins, and execute affected commands. |
| Each release | Choose explicit package identity/version, build/check the wheel, retain its owner binding and digest, and hand off artifacts. |
| Each new platform or layout | Check backend/bootstrap coverage and URL/hash/archive layout, supply missing metadata, then execute freshly prepared tools on the platform. |
| Each user update | Change only the facade release requirement and lock/sync, or reprovision the existing native selection. |

`refresh.sh`, `refresh.py`, `python_package.py`, `provision.py`, and the
bootstrap retain distinct required roles. No helper is redundant in this
workflow. The old Git-selected `score-tool` usage instructions are superseded
by ordinary wheel extras; its existing entrypoint and root package remain for
compatibility. The public Bazel targets and `run-tool` fallback also remain.
Historical reports are evidence and are not release/update dependencies.
