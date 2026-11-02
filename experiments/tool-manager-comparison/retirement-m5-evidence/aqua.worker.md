<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Aqua maintenance ledger — milestone 5

## Outcome

Native and Python selections are installed directly from their current owners
during the DevContainer image build and by a one-time host prefix provisioning
command. Runtime tool invocations use the installed executables. The root
portable lockfiles, generated Python catalog, existing Bazel labels and runner
arguments remain compatibility interfaces.

The published selection keeps the exact existing decisions for APM 0.35.0,
OpenCode 2.2.3, starpls 0.1.22 and codespell 2.4.1. Other selected versions
were retained. The ordinary `uv`/`uvx` workflows and APT, npm, special provider,
and complex external tool integrations remain available.

## Removal and caller ledger

| Area | M5 result | Ongoing responsibility |
| --- | --- | --- |
| `tools/internal/devcontainer/install.py` | Removed native network download, checksum verification, archive extraction, Python tool installation, prepared-manifest handling, and `install` / `install-python` commands. Kept catalog version/selection/metadata inspection, APT and npm lifecycle, and environment verification. | Keep provider setup and installed-state inspection separate from image provisioning. |
| `tools/run-tool` | Strict host mode resolves the provisioned executable directly; container mode uses image PATH. Both retain the Bazel fallback when the direct command is unavailable. | Normal prepared calls go straight to binaries; fallback remains for missing commands and compatibility. |
| `.devcontainer/post_create_command.sh` | The generic JavaScript/Node DevContainer provisions the repository profile into the current user's host prefix before applying repository providers and registering pre-commit. | The owner fingerprint makes repeated post-create runs a no-op while the selected prefix is current. |
| Root `.devcontainer/devcontainer.json` | Adds the provisioned prefix to remote `PATH` and sets `SCORE_TOOLS_BIN`, so hook and interactive processes see the same tools. | Keep remote path and provisioner prefix in sync. |
| `s-core-local` and `bazel-feature` installers | Their lifecycle calls still select and configure providers, but no longer fetch or unpack native/Python tools. | Keep APT setup, CodeQL and Bazel-related external installation/configuration with their existing owners. |
| Default Dockerfiles | Both variants invoke the same owner-driven published provisioning path for the target Linux architecture. Aqua and uv are build-time tools; only installed tools remain in `/opt/score-tools`. | New images provision their own inputs. No manually generated runtime handoff is required. |
| M3 prepared-runtime handoff | Deleted `check_devcontainer.py`, the staging option and handoff test. Removed the large ignored `.devcontainer/prepared-tools` output and its ignore rule. | There is no prepared manifest or producer cache contract in production. |
| Root Bazel compatibility | Existing labels, runner CLI, cwd and exit behavior are preserved. Native portable URLs/hashes/layouts and Python version pins are regenerated from Aqua and Python owners. | `export_native.py` remains a bounded archive/raw-file adapter for the current lock schema; keep it aligned if an upstream layout changes. |
| Update automation | Renovate uses the pinned Aqua preset for the production Aqua YAML, PEP 621 for Python dependency groups, and a single bootstrap-version manager; daily allowlist and post-upgrade command both point to `tools/internal/aqua/refresh_owners.py`. | The refresh updates bootstrap hashes, Aqua checksums, root compatibility outputs and generated tool docs. `experiments/**` is excluded from owner discovery. |
| Local reference release | `prepare.py`, the standard wheel extras and local image/check scripts remain usable; APM runtime copying is kept in the release producer too. | These are local candidate evidence tools; no package/image is published. |

## Maintained owners and adapters

- `tools/owners/aqua/aqua.yaml` owns selected native versions and tags. Aqua
  registry checksums are refreshed in `aqua-checksums.json` beside it.
- `tools/owners/aqua/pyproject.toml` dependency groups own Python versions and
  profiles.
- `apm-registry.yaml` and `starpls-registry.yaml` provide the pinned local
  recipes missing from standard registry v4.579.0. `aqua-policy.yaml` allows
  those exact local identities.
- APM needs its complete expanded directory beside the executable. The image
  and host provisioners copy that directory under `lib/apm` and expose a
  relative `bin/apm` link; copying only the raw binary is insufficient.
- OpenCode uses its standard registry recipe at exactly 2.2.3. Its checksum
  exporter reads aqua's `http/opencode.ai` checksum identity while preserving
  the existing portable root GitHub asset URLs.
- `tools/owners/aqua/aqua-bootstrap.toml` owns aqua 2.65.2 artifact checksums for Linux amd64,
  Linux arm64, macOS amd64 and macOS arm64. The bootstrap is downloaded only
  for provisioning and removed from the image build layer's final filesystem.
- `tools/internal/aqua/sync_repository.py`, `export_native.py` and
  `refresh_owners.py` produce the
  current portable native lockfiles, Python catalog, environment membership,
  uv Bazel helper, and tool documentation. They do not own package versions.
- `tools/lockfiles/README.md` documents generated root lock metadata. Existing
  APT/provider catalog entries and feature-specific complex tools stay with
  their established installers.

## One-time work and recurring work

Adding a standard-registry native tool requires an owner entry and environment
tag. A tool outside the root lock schema may also need a bounded exporter
mapping or new compatibility metadata. A missing registry package needs a
reviewed local recipe and policy entry. A Python CLI needs a pinned dependency
group requirement plus generated command identity metadata. These are
integration steps for the tool's interface, not another install engine.

For an owner update, edit the owner file, run
`python3 tools/internal/aqua/refresh_owners.py`, review the generated root
lock/catalog/environment/docs changes, and run the checks below. CI uses that
same refresh path for Renovate updates. Host users rerun
`tools/internal/devcontainer/provision_host_tools.py` to refresh their direct
prefix; the default is `~/.local/share/score-tools`. Standalone host users add
that prefix's `bin` directory to `PATH` in their shell startup file for ordinary
`uv`/`uvx` and tool calls. The root Node DevContainer provisions it at
post-create and sets it through `remoteEnv`. Feature-image consumers get the
published selection through a normal image build.

## Checks and platform scope

These are the bounded checks completed against the current production owners
and candidate source. A passing syntax or metadata check does not imply that an
image was built or a binary was executed on that architecture.

| Check | Command or evidence | Result |
| --- | --- | --- |
| Owner refresh and generated-output freshness | `AQUA_BINARY=/tmp/score-aqua-eval/bootstrap/aqua AQUA_ROOT_DIR=/tmp/score-m5-aqua/aqua-root-refresh python3 tools/internal/aqua/refresh_owners.py`; then `python3 tools/internal/aqua/sync_repository.py --check` and `python3 tools/internal/sync_readme.py --check` | All exit 0. Refresh reported `"changed": []`; sync check reported `"changed": []`; README check was clean. |
| Removed-engine audit | `rg -n 'install-python|install\.py install|_cmd_install|_extract_member|_extract_dir|_place_binary|SCORE_PREPARED_TOOLS|prepared-tools|stage-devcontainer|check_devcontainer|refresh_lockfile_digests' tools .devcontainer src/s-core-devcontainer .github --glob '!README-m4.md'` | Exit 1 with no matches, as expected. No active retired install/extract/staging caller or implementation was found in those production paths. |
| Python syntax | `python3 -m py_compile tools/internal/devcontainer/provision_host_tools.py tools/internal/devcontainer/bootstrap_aqua.py tools/internal/aqua/refresh_owners.py tools/internal/aqua/sync_repository.py tools/internal/aqua/export_native.py experiments/tool-manager-aqua/reference/prepare.py experiments/tool-manager-aqua/reference/check.py tools/tests/test_refresh_owners.py tools/score_tools/catalog.py` | Exit 0. |
| Python unit tests | `python3 -m unittest discover -s tools/tests -p 'test_*.py'` | 20 tests passed. This includes repeated bootstrap checksum refresh preserving unrelated archive sections. |
| Ruff, formatting, and ShellCheck | `/tmp/score-m5-aqua/host-tools/bin/ruff check tools/internal/devcontainer/provision_host_tools.py tools/internal/devcontainer/bootstrap_aqua.py tools/internal/aqua/refresh_owners.py tools/internal/aqua/sync_repository.py tools/internal/aqua/export_native.py experiments/tool-manager-aqua/reference/prepare.py experiments/tool-manager-aqua/reference/check.py tools/tests/test_refresh_owners.py tools/score_tools/catalog.py`; matching `ruff format --check` on those files; `/tmp/score-m5-aqua/host-tools/bin/shellcheck .devcontainer/post_create_command.sh tools/run-tool tools/tests/run_tool_test.sh tools/tests/python_tool_runner_test.sh src/s-core-devcontainer/.devcontainer/bazel-feature/install.sh src/s-core-devcontainer/.devcontainer/s-core-local/install.sh tools/internal/devcontainer/provision_image_tools.sh` | All exit 0. Ruff passed; 9 Python files were already formatted; ShellCheck was clean. |
| Bazel runner compatibility | `bazel --output_base=/tmp/score-m5-aqua/bazel test //tools:run_tool_test //tools:python_tool_runner_test` | Exit 0; both tests passed from cache. Bazel printed its test-size warning. Tests cover direct strict execution, cwd/argv and exit forwarding, and missing-command Bazel fallback. |
| Existing Bazel public targets | `bazel --output_base=/tmp/score-m5-aqua/bazel run //tools:apm -- --version`; `bazel --output_base=/tmp/score-m5-aqua/bazel run //tools:opencode -- --version`; `bazel --output_base=/tmp/score-m5-aqua/bazel run //tools:starpls -- version`; `bazel --output_base=/tmp/score-m5-aqua/bazel run //tools:codespell -- --version` | All exit 0: APM 0.35.0, OpenCode 2.2.3, starpls 0.1.22, codespell 2.4.1. |
| Pinned host bootstrap and prefix reuse | `env -u AQUA_BINARY PATH=/usr/bin:/bin AQUA_ROOT_DIR=/tmp/score-m5-aqua/aqua-root-host UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host python3 tools/internal/devcontainer/provision_host_tools.py --profile published --prefix /tmp/score-m5-aqua/host-tools` | Aqua 2.65.2 was checksum-bootstrapped into the prefix during initial provisioning. Final restricted-PATH run reported `status: current`, proving the production owner digest and selected commands were reusable without Aqua on PATH. |
| Direct published host commands | With `PATH=/usr/bin:/bin SCORE_TOOLS_BIN=/tmp/score-m5-aqua/host-tools/bin RUN_TOOL_CONTAINER_MODE=host`, ran `tools/run-tool --strict apm --version`, `... opencode --version`, and `... codespell --version` | Exit 0: APM 0.35.0, OpenCode 2.2.3, codespell 2.4.1. `bin/apm` is a symlink into `lib/apm`; executable and `_internal` runtime directory are present. |
| Ordinary uvx consumption | `PATH=/tmp/score-m5-aqua/host-tools/bin:/usr/bin:/bin UV_CACHE_DIR=/tmp/score-m5-aqua/uv-cache-host uvx --offline --from codespell==2.4.1 codespell --version` | Exit 0; printed 2.4.1 using the retained prefix and local cache. |
| Root post-create wiring | `npm exec --yes --package=@devcontainers/cli -- devcontainer read-configuration --workspace-folder .`; plus ShellCheck of `.devcontainer/post_create_command.sh` | Parse exit 0. Resolved config contains persistent `remoteEnv` PATH and `SCORE_TOOLS_BIN`; post-create invokes the repository provisioner before provider setup. The full post-create command was not run. |
| Editor-configured starpls | Read `bazel.lsp.command` from `src/s-core-devcontainer/.devcontainer/devcontainer.json`, then ran `docker run --rm --network none --mount type=bind,source=/tmp/score-m5-aqua/host-tools,target=/opt/score-tools,readonly --entrypoint /opt/score-tools/bin/starpls buildpack-deps:noble-curl version` | Exit 0; the configured `/opt/score-tools/bin/starpls` printed version 0.1.22 against an existing local base image. This was not an image build. |
| Full production image | `npm exec --yes --package=@devcontainers/cli -- devcontainer build --workspace-folder src/s-core-devcontainer --image-name score-aqua-m5:linux-amd64 --platform linux/amd64` | A candidate attempt was interrupted and produced no completion result. It was not retried after the disk constraint; root owns image scheduling. No successful image build is claimed. |
| Platform runtime scope | Runtime commands above were executed on this Linux amd64 host. Owner/bootstrap metadata includes Linux arm64 and macOS artifacts where declared. | Linux arm64 and macOS binaries were not executed here; metadata is not runtime validation. |

## Limitations

The current native exporter deliberately supports known portable lockfile
layouts; it is not a generic Aqua-to-Multitool converter. Local recipes and
APM runtime copying are explicit integration responsibilities. A successful
Linux amd64 build does not establish Linux arm64 or either macOS runtime. Any
unavailable build or test is reported with its command and result, without a
claim that it passed. The current source and focused checks are complete, while
the production-image gate and cross-platform runtime checks remain unverified.
