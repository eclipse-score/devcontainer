<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# What mise can retire from the SCORE installer

**Historical pre-M5 assessment.** Its caller and deletion tables record work
that was still outstanding when the report was written. M5 completed that work;
see [the final implementation ledger](README-m5.md) for current behavior and
remaining limitations.

Investigation date: 2026-11-01. This report covers the public `etas-contrib`
checkout only. It records evidence and a retirement boundary; it does not claim
that the installers or M1–M4 artifacts have been changed.

## Conclusion

Mise can install the two remaining native tools at their current pins. The
existing pinned mise 2026.10.24 GitHub backend installed APM 0.35.0, and its Aqua backend
installed OpenCode 2.2.3. The task-owned four-platform lock resolved all eight
artifact hashes to the existing native catalog's hashes. This is not literal
URL equality: the mise OpenCode route uses `opencode.ai`, while the existing
catalog points to the GitHub release. The Linux x86_64 archives from those two
URLs were downloaded and their hashes matched. No alternate tool version or
local backend recipe was needed. For OpenCode, use the explicit
`aqua:anomalyco/opencode` backend: the registry's bare `opencode` shorthand
prefers `npm:@opencode/cli` first. Mise documents explicit backend identifiers in its
[backend architecture](https://mise.jdx.dev/dev-tools/backend_architecture.html)
and [backend list](https://mise.jdx.dev/cli/backends.html). The exact upstream
releases are [APM v0.35.0](https://github.com/microsoft/apm/releases/tag/v0.35.0)
and [OpenCode v2.2.3](https://github.com/anomalyco/opencode/releases/tag/v2.2.3).

That resolves package availability; it does not retire any code in the current
prototype. `s-core-local` selects both tools, while the prepared selection omits
them, so the feature installer still sends them through the catalog download
and extraction path. The repository `post_create_command.sh` also invokes the
legacy environment installer without a prepared handoff. The prepared-runtime
producer currently bypasses some catalog installs, but it retains both the
fallback and a second producer/handoff path.

For a future mise migration whose purpose is deleting our installer logic, the
smallest coherent target is direct mise provisioning in the existing feature
and repository setup lifecycles. After every caller moves, that allows deleting
the custom native download/extract path and the `uv tool install` image path.
The current producer handoff can also be removed in that design. Keep the
managerless consolidated baseline as the default until this migration reaches
that deletion boundary; the current M4 handoff is not evidence of reduced
maintenance effort. If the team proceeds with mise, prefer the direct lifecycle
route over making the handoff permanent.

This is a technical recommendation, not an engineering-hours estimate. Only
Linux x86_64 was prepared and executed. The three other platform results below
are locked metadata comparisons, not cross-platform executions.

## Pinned native route evidence

The temporary configuration was copied from
[`mise.native.toml`](mise.native.toml) into `/tmp/score-retirement-mise`, then
extended there with the two exact native owners. The checked-in M4 config and
snapshots were not edited. The manager binary was the existing pinned artifact
at `/tmp/score-m4-mise/bootstrap-check/mise`: `2026.10.24 linux-x64`, SHA-256
`be97dbac1c0b1fe08bd8c0cf01690f4273ea9aa02ad766b98d4e20c43eb9059d`.

| Tool | Explicit mise owner | Existing pin | Actual result |
| --- | --- | --- | --- |
| APM | `github:microsoft/apm` | `0.35.0` | Installed from `apm-linux-x86_64.tar.gz`; installed CLI reports `0.35.0`. |
| OpenCode | `aqua:anomalyco/opencode` | `2.2.3` | Installed from the Aqua route's `opencode.ai` archive; CLI reports `v2.2.3`. |

Commands run with task-owned `MISE_CONFIG_DIR`, `MISE_CACHE_DIR`, `MISE_STATE_DIR`,
and `MISE_DATA_DIR`:

```sh
/tmp/score-m4-mise/bootstrap-check/mise \
  -C /tmp/score-retirement-mise -E native install --verbose \
  github:microsoft/apm aqua:anomalyco/opencode

/tmp/score-m4-mise/bootstrap-check/mise \
  -C /tmp/score-retirement-mise -E native lock \
  --platform linux-x64,linux-arm64,macos-arm64,macos-x64 \
  github:microsoft/apm aqua:anomalyco/opencode
```

The first command required network access to `mise-versions.jdx.dev`, GitHub,
and `opencode.ai`; both installs completed. The second checked eight tool/platform
entries and wrote only `/tmp/score-retirement-mise/mise.native.lock`. The locked
SHA-256 values match all four platform artifacts in each existing lockfile:
[`apm.lock.json`](../../../tools/lockfiles/apm.lock.json) and
[`opencode.lock.json`](../../../tools/lockfiles/opencode.lock.json). The Aqua
OpenCode URL differs from its legacy GitHub URL, but the Linux archive hashes
are identical. The exact archive hashes and invocation results are in
[`retirement.json`](evidence/retirement.json).

APM needs its full install tree. The archive contains `apm` plus `_internal/`
with `libpython3.12.so.1.0`, the Python standard library, bundled dependencies,
and templates; the installed tree is 24 MiB. `apm --version`, `apm --help`, and
`apm install --help` succeeded with the normal `/usr/bin:/bin` path; the version
and `install --help` commands also worked through a task-owned symlink to the
manager-installed executable. A task-only copy of the ELF with `_internal/`
removed failed with exit 255 while loading `libpython3.12.so.1.0`. With an empty `PATH`,
help failed during GitPython import because `git` was not found. Setting
`GIT_PYTHON_GIT_EXECUTABLE=/usr/bin/git` made the help command succeed even with
an empty `PATH`. The existing `s-core-local` selection already installs Git
through APT. APM does not need a separate Python installation, but copying only
the `apm` ELF and dropping `_internal/` would break the runtime. Its real package
install, credential, and network workflows were not exercised.

OpenCode installs as one 252 MB Linux ELF (241 MiB on disk). `--version` and
`--help` both succeeded with an empty `PATH` through a task-owned symlink. It
uses the host's normal Linux C runtime; no mise, npm, uv, or Python launcher is
in the command chain. Interactive/server, model-provider, and update flows were
not exercised.

## Actual callers and compatibility boundary

The [s-core-local feature](../../../src/s-core-devcontainer/.devcontainer/s-core-local/install.sh#L44)
executes `install.py environment s-core-local --prepared-manifest`. The
selection in [`tools/environments.json`](../../../tools/environments.json#L2)
contains APM and OpenCode, but
[`tools/prepared-selection.json`](../../../tools/prepared-selection.json#L4)
does not. `_cmd_environment` therefore verifies the available handoff, skips
only its listed tools, and passes the remaining native names to `_cmd_install`.
The existing regression asserts exactly that fallback:
[`prepared_runtime_test.sh`](../../../tools/tests/prepared_runtime_test.sh#L132-L145).

The [bazel-feature installer](../../../src/s-core-devcontainer/.devcontainer/bazel-feature/install.sh#L38)
also calls `environment` with a manifest. It owns Bazelisk, Buildifier and
Starpls selection; it does not own APM or OpenCode. The repository's
[post-create hook](../../../.devcontainer/post_create_command.sh#L21) calls
`environment repository` without a manifest, then installs pre-commit hooks.
That environment still selects eight native tools and pre-commit. Its current
call reaches `_cmd_install` and `_cmd_install_python` even though those tools
already have mise owners. Migrating only APM and OpenCode cannot remove the
installer functions while this caller remains.

The root caller audit also records feature build/cleanup phases, which manage
temporary APT packages; `load_feature_versions.sh` and optional `install_dive`
metadata/provider-version queries; feature verification; the Python-runner
regression; and Renovate's post-upgrade task plus daily command allow-list.
Those metadata, APT lifecycle, behavior-check, and update-automation duties
must remain or be migrated deliberately, but they do not require the native
archive download/extract functions themselves. See the root's
[tracked-caller inventory](../../../../score_devcontainer/experiments/tool-manager-comparison/retirement-evidence/baseline.callers.json).

The installer file is under `tools/internal`; its subcommands are not stated as
a public compatibility API. The internal README describes it as a container
installer, and Bazel uses it as test data rather than exporting it as a public
label. Its usage banner and regression tests still document internal behavior,
and the feature scripts above are real callers that must be migrated before
removing a subcommand. Public compatibility is instead explicit for the
[`//tools:apm` and `//tools:opencode` Bazel aliases](../../../tools/BUILD.bazel#L19-L52),
the exported native lockfiles, and the [`run-tool` interface](../../../tools/run-tool#L54-L73).
Keep those host paths: container `run-tool` execs the installed PATH command;
non-strict host mode prefers PATH; strict host mode uses the pinned Bazel
label. Argument forwarding, caller cwd, exit status and the container's trust
in its installed pins remain as documented.

The prepared M4 process chain is also direct after setup. Native Starpls is an
ELF command; prepared Python console scripts have absolute shebangs under
`/opt/score-tools/prepared-runtime/data/.../bin/python`, which resolves to the
image's `/usr/bin/python3`. A Python interpreter is part of that CLI's runtime,
but mise and uv are not launched for each container command. The existing
Bazel-host Python target does invoke its pinned `uvx --from package==version`
launcher after `bazel run`; that is existing strict-host delivery behavior and
is not changed by retiring the container installer. Do not expose mise shims,
`mise exec`, or an uv resolver as the required container invocation path.

## What can disappear, what stays, and what moves

| Surface | Retirement result | Condition or reason |
| --- | --- | --- |
| `_cmd_install`, `_place_binary`, `_extract_member`, `_extract_dir`, download/checksum logic and `install` parser in [`install.py`](../../../tools/internal/devcontainer/install.py#L193-L295) | **Delete after migration.** | Every native member of `s-core-local`, `bazel-feature`, and `repository` must be provisioned by mise in its actual setup lifecycle. Migrate the root post-create caller as well as both features. |
| `_cmd_install_python` and `install-python` parser in [`install.py`](../../../tools/internal/devcontainer/install.py#L153-L190) | **Delete after migration.** | All current Python selections must be provisioned by mise, including repository pre-commit. Keep the generated Python catalog/uvx host target for Bazel compatibility. |
| `_load_prepared_handoff`, `prepared-selection.json`, prepared skip/fallback behavior and its test | **Delete for the direct lifecycle design.** | They exist to validate a separate producer-to-image transfer. If the handoff is kept, they remain, and the old installer is still needed for any missing member. |
| `environment` selection, APT provider installation, feature metadata, Java/CodeQL setup, and other feature lifecycle hooks | **Keep.** | Mise does not replace APT, CodeQL pack downloads, Java environment setup, or Dev Container feature behavior. `install.py` can remain as the internal APT/selection helper after its CLI-install subcommands go. |
| `//tools:<native>` labels, `run-tool`, exported native JSON and Python Starlark catalogs | **Keep as public compatibility outputs.** | Strict host delivery and downstream Bazel consumers still need pinned artifacts and existing labels. The native lockfiles are exported from `tools/BUILD.bazel`. |
| Artifact URL, digest, supported platform, command name, and archive-member knowledge | **Move into the existing Bazel metadata exporter.** | It remains necessary for `rules_multitool`; derive URLs and hashes from `mise.lock`, while keeping a bounded layout map. For APM, preserve its full archive root (`apm-linux-x86_64/`) and `_internal/` runtime. For OpenCode, add zip handling for macOS as well as the Linux tar members. Preserve all four existing platforms per tool. |
| `refresh_lockfile_digests.py` and its Renovate allow-list entry | **Delete only after generated lock export owns every native lock.** | The existing daily Renovate regex managers target JSON lockfiles and invoke this refresh helper. Move version updates to the mise owner/lock and run the exporter before deleting the old updater. Keep `sync_readme.py` for generated inventory. |
| `prepare-production.sh`, the producer copy of `mise`, `provision.py` handoff generation, BuildKit named context, Docker `COPY --from=score_mise_runtime`, and the `scripts/build.sh` context gate | **Optional experimental machinery; remove for direct provisioning.** | These make sense only if tools are intentionally prepared out of band. They add a second build input, runtime manifest/hash checks, owner freshness checks and cross-stage copying. The existing handoff can remain an experiment but should not be required for installer retirement. |

There is specific exporter work before a generated Bazel route is safe. Current
[`prepare.py`](prepare.py#L36-L45) has no APM/OpenCode backend entries;
[`provision.py`](provision.py#L73-L86) has no command map for them. Its exporter
filters to Linux x64/arm64 and macOS arm64, asserts three artifacts, handles tar
and tar.xz but not zip, and does not preserve APM's whole archive directory
([`prepare.py`](prepare.py#L48-L100)). A mechanical addition would either omit
the existing macOS x86_64 Bazel support or produce an incomplete APM package.
Add only the two explicit backend/command/layout mappings and preserve their
four existing supported platforms; keep the rest of the existing bounded
adapter rather than creating a new packaging schema.

## Direct feature provisioning versus producer handoff

| | Direct manager provisioning in existing setup lifecycles | Current prepared-runtime producer handoff |
| --- | --- | --- |
| Native/Python install location | Each feature provisions its selected tools with the pinned manager at build time. Repository setup does the same for its selected tools. Use direct executable symlinks/paths, not manager shims. | A producer installs to a separate prefix, exports a manifest and executable links, then a Docker named context copies the prefix into the image. |
| Installer deletion | Once both features and `post_create_command.sh` have moved, delete `_cmd_install` and `_cmd_install_python`; no per-tool fallback remains. | Add APM/OpenCode to both adapter maps and prepared selection, then also migrate the repository root caller. Only when every native/Python selection is handed off can the installer paths be deleted. |
| Mise-specific code | Keep the pinned manager bootstrap and a small provisioning/path adapter used only during setup. Keep the existing Bazel/Python compatibility exporter. | Keep the manager bootstrap, producer orchestration, full runtime export, manifest generation, stale-input checks, skip logic, prepared-runtime tests and Docker handoff. |
| Ordinary container command | `run-tool` execs the installed command. Native tools stay direct; Python tools use their installed console entrypoint and required interpreter. No manager/resolver is mandatory per call. | Same direct invocation after successful handoff validation. The manager stays in the producer, not in the call chain. |
| Remaining limitation | Feature builds and repository setup need manager network access unless their surrounding build supplies it. APM still needs Git at runtime. | Requires a fresh matching producer/context before image build and has only been exercised on Linux amd64 so far. |

The direct route needs one-time work: make the pinned mise binary available to the
feature and repository setup paths; have the existing environment membership
select which configured backend IDs to install; create direct PATH entries that
keep complete install trees such as APM's `_internal`; then migrate both feature
scripts and the repository post-create hook. Python tools need stable venv paths
and their required system Python. This reuses the current environment selection
and bounded executable map; it does not require a new general schema.

For normal updates, change the exact owner in the mise config, refresh/verify its
multi-platform `mise.lock`, regenerate the current Bazel lock and Python metadata
outputs, and re-sync the tool README. Renovate must update the owner and run that
export path; the current config only updates APM/OpenCode JSON lock versions and
allows `refresh_lockfile_digests.py`, so the automation is not migrated yet. For
a new native tool, add an explicit backend/version and environment membership,
add a bounded executable/layout mapping only if the exporter cannot infer it,
then check the resulting public Bazel target and direct installed command.
Neither current APM nor OpenCode needs a local override. A future backend with
no upstream package can use an explicit generic `github:`/`aqua:` route only
when its release assets resolve and lock at the requested version; otherwise
record a local recipe and own its update/layout maintenance. Do not silently
select a different package version.

## Commands and test status

| Check | Command | Result |
| --- | --- | --- |
| Manager installation | `mise -C /tmp/score-retirement-mise -E native install --verbose github:microsoft/apm aqua:anomalyco/opencode` | Both existing exact pins installed; network enabled and used. |
| Platform lock | `mise -C /tmp/score-retirement-mise -E native lock --platform linux-x64,linux-arm64,macos-arm64,macos-x64 github:microsoft/apm aqua:anomalyco/opencode` | Eight entries resolved; all platform artifact hashes matched the legacy catalog. The OpenCode URL differs (`opencode.ai` vs GitHub); both Linux x86_64 archives were fetched and had the same hash. |
| APM CLI | `/tmp/score-retirement-mise/bin/apm --version`; `/tmp/score-retirement-mise/data/installs/github-microsoft-apm/0.35.0/apm --help`; `/tmp/score-retirement-mise/bin/apm install --help` | Version `0.35.0`; direct executable/symlink help succeeds when Git is available. Empty PATH fails without Git; explicit GitPython path succeeds. Copying only the ELF fails because adjacent `_internal/libpython3.12.so.1.0` is required. |
| OpenCode CLI | `/tmp/score-retirement-mise/bin/opencode --version`; `/tmp/score-retirement-mise/bin/opencode --help` | Version `2.2.3`; both succeed with an empty PATH. |
| Artifact bytes | SHA-256 of the downloaded Linux x64 APM and OpenCode release archives | Both equal their current lockfile digests; the Aqua OpenCode archive equals the GitHub archive bytes. |

These are installation and command checks, not a repository test suite. No
repository tests were run. The current prepared-runtime regression still expects
`["apm", "opencode"]` to reach `_cmd_install`; after migration, replace that
expectation with a setup-time direct-path/version check. Preserve the existing
host contracts with `bazel test //tools:run_tool_test //tools:python_tool_runner_test`
and the Python catalog suite `python3 -m unittest discover -s tools/tests -p 'test_*.py'`.

## Comparison with the managerless target and peer probes

The root follow-up recommends the consolidated managerless architecture for
the current project scope. The evidence supports that project-wide choice:
the same portable native catalog already feeds the container installer and
public Bazel targets; the baseline installed Ruff 0.11.13, ShellCheck 0.10.0,
and Starpls 0.1.22, plus pre-commit 4.7.0 through its existing uv adapter, in
task-owned directories; and direct commands plus Ruff/ShellCheck/pre-commit
checks succeeded. This keeps one source of artifact metadata while Python
release output remains common work across candidates.

| Variant | Current exact-pin evidence for the remaining tools | Concrete limit |
| --- | --- | --- |
| Managerless baseline | Existing catalog installs were exercised for representative native and Python tools. A real temporary ShellCheck 0.11.0 update fetched upstream metadata, refreshed the version-bearing archive fields, downloaded and verified the Linux artifact, extracted it, and ran `--version`. | The custom download/extract/checksum and refresh implementation remains. The file/dir version-bearing update defect is now repaired and covered; it is not an unresolved reason to adopt a manager. The proof does not establish arbitrary layout support or completed standalone-host/release integration. |
| mise | This probe installed exact APM 0.35.0 and OpenCode 2.2.3. Its four-platform hashes match the catalog, while OpenCode's `opencode.ai` URLs differ from the catalog's GitHub URLs. Only Linux x86_64 was downloaded and executed. | Does not migrate current callers or eliminate the Bazel metadata exporter, lock exports, Renovate work, or runtime Git requirement for APM. No all-platform execution was done. |
| aqua | The peer retirement probe installed exact OpenCode 2.2.3 and APM 0.35.0 on Linux amd64. Its OpenCode `opencode.ai` asset has the same Linux archive hash as the catalog's GitHub URL. The pinned standard registry lacks APM, so it used a task-local generated/reviewed recipe. APM requires retaining its full package tree: copying only the executable fails; direct-tree `--version`, `--help`, and read-only `init --discover` succeeded. | Adds APM recipe/policy/layout maintenance. The exact runtime check does not cover APM's credentialed/network install flow or other platforms. Aqua's default proxy is not the direct invocation path. |
| Nix | The peer correction confirms `pkgs.apm-cli` is already exactly 0.35.0. Locked `pkgs.opencode` is 2.2.1; a task-local Linux x86_64 binary derivation from the existing 2.2.3 release asset and digest succeeded with `dontStrip = true`, and `--version`/`--help` passed. | Exact OpenCode 2.2.3 is a local package/version intervention, not the locked package result; no all-platform or source-build support was proved. M4 Codespell 2.4.3 also differs from the 2.4.1 pin used by mise/aqua. |

The evidence sources cross-read for this reconciliation are the root
[`tooling-installer-retirement.md`](../../../../score_devcontainer/docs/tooling-installer-retirement.md),
the Aqua peer report at
`/tmp/score-retirement-aqua/reference/README-retirement.md`, the common findings
at `/tmp/score-retirement-common/root-findings.md`, and the Nix peer note at
`/tmp/score-retirement-nix/root-note.md`. The earlier peer M4 summaries remain
useful for lifecycle context, but their M4-only description that APM/OpenCode
had no candidate-native route is superseded by these task-owned probes.

## Recommendation and limits

The root's managerless recommendation follows from the observed scope, but it is
not the only defensible criterion. This repository must preserve portable
artifact descriptions for public Bazel targets regardless of container install
engine. The managerless path already reuses that catalog, has a working
representative install/update flow, and avoids adding a second owner plus a
lock-to-Bazel export and Renovate lifecycle. The ShellCheck defect cited by the
earlier version of this report is repaired: its `file` and `dir` update cases
now pass regression coverage, and an actual temporary update to ShellCheck
0.11.0 fetched, verified, extracted, and ran successfully. The production pin
was not changed.

The material counterargument is narrower and real: managerless keeps our custom
native downloader, archive extraction, and checksum refresh code. Direct mise
provisioning can replace that engine after migrating the feature and repository
callers, and exact APM/OpenCode installs required no local mise recipe. If the
decision criterion is specifically retiring that implementation, mise is the
strongest observed manager alternative. Its direct installed executables also
avoid a manager/resolver on ordinary container invocation; APM still needs Git
and its complete bundled `_internal` runtime. Aqua is workable but needed a
local APM recipe and whole-tree handling. Nix is workable but exact OpenCode
2.2.3 required a separate Linux binary derivation while the locked package was
2.2.1. None of these probes demonstrates that new manager/export/update work is
less effort than maintaining the repaired baseline, and none migrates the
callers in this report.

Accordingly, this report records mise as the strongest manager alternative,
not as an adoption recommendation. Under the current broader requirements, the
root's consolidated managerless target is the defensible default. If reducing
our own native install implementation becomes the controlling requirement,
direct mise provisioning is a concrete alternative to evaluate; the existing
producer handoff plus legacy fallback does not accomplish that retirement.

The peer probes and this probe are bounded Linux x86_64/amd64 command evidence,
except where the mise task resolved four-platform lock metadata. No peer
comparison established all-platform execution, a complete product workflow,
release/host integration, engineering hours, or a universal package-coverage
result. The root warm-start observation is not included as a manager ranking.
No manager was adopted and no M1–M4 owner or artifact was edited.

The existing comparison records remain the broader decision basis:
[`tooling-effort-conclusion.md`](../../../../score_devcontainer/docs/tooling-effort-conclusion.md)
and
[`tooling-execution-paths.md`](../../../../score_devcontainer/docs/tooling-execution-paths.md).
This probe did not rebuild an image, run repository test suites, mutate Docker,
measure startup timing, or edit any M1–M4 owner/artifact.
