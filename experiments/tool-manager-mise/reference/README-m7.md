<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Mise M7: Linux ARM64 selected tool execution

**Status, 2026-11-02:** the current published native and Python selection was
installed into a fresh mise prefix and exercised as Linux ARM64 under QEMU.
Selected pins were unchanged. The runtime and wheel consumer checks ran as
`uid=1000`, with networking disabled and a read-only root filesystem. The
M7-specific Bazelisk check stopped at the configured no-fallback guard, so no
Bazel download or run was counted. macOS ARM configuration was reviewed but
not executed. This is candidate evidence; it makes no winner or adoption claim.

The root-owned comparison gate report records all six M6 gates passed. Root
owns the shared comparison and archives these results after candidate work.

## Selection and provenance

The published platform profile is the union of `s-core-local` and
`bazel-feature` in `tools/environments.json`. Mise installed the 9 entries in
`tools/mise/mise.native.toml`, the published-only Starpls entry, and the 4
PyPI entries from `tools/mise/mise.python.toml`. This yields 15 exposed
commands because uv provides both `uv` and `uvx`:

| Command | Selected version | Prepared executable |
| --- | ---: | --- |
| actionlint | 1.7.7 | `/tmp/score-m7-mise/runtime/data/installs/aqua-rhysd-actionlint/1.7.7/actionlint` |
| apm | 0.35.0 | `/tmp/score-m7-mise/runtime/data/installs/github-microsoft-apm/0.35.0/apm` |
| bazelisk | 1.27.0 | `/tmp/score-m7-mise/runtime/data/installs/aqua-bazelbuild-bazelisk/1.27.0/bazelisk` |
| basedpyright | 1.35.0 | `/tmp/score-m7-mise/runtime/data/installs/pypi-basedpyright/1.35.0/basedpyright/bin/basedpyright` |
| buildifier | 8.2.1 | `/tmp/score-m7-mise/runtime/data/installs/aqua-bazelbuild-buildtools-buildifier/8.2.1/buildifier` |
| codespell | 2.4.1 | `/tmp/score-m7-mise/runtime/data/installs/pypi-codespell/2.4.1/codespell/bin/codespell` |
| opencode | 2.2.3 | `/tmp/score-m7-mise/runtime/data/installs/aqua-anomalyco-opencode/2.2.3/opencode` |
| pre-commit | 4.7.0 | `/tmp/score-m7-mise/runtime/data/installs/pypi-pre-commit/4.7.0/pre-commit/bin/pre-commit` |
| pytest | 9.0.2 | `/tmp/score-m7-mise/runtime/data/installs/pypi-pytest/9.0.2/pytest/bin/pytest` |
| ruff | 0.11.13 | `/tmp/score-m7-mise/runtime/data/installs/aqua-astral-sh-ruff/0.11.13/ruff-aarch64-unknown-linux-gnu/ruff` |
| shellcheck | 0.10.0 | `/tmp/score-m7-mise/runtime/data/installs/aqua-koalaman-shellcheck/0.10.0/shellcheck-v0.10.0/shellcheck` |
| starpls | 0.1.22 | `/tmp/score-m7-mise/runtime/data/installs/github-withered-magic-starpls/0.1.22/starpls` |
| uv | 0.13.6 | `/tmp/score-m7-mise/runtime/data/installs/uv/0.13.6/uv-aarch64-unknown-linux-gnu/uv` |
| uvx | 0.13.6 | `/tmp/score-m7-mise/runtime/data/installs/uv/0.13.6/uv-aarch64-unknown-linux-gnu/uvx` |
| yamlfmt | 0.17.0 | `/tmp/score-m7-mise/runtime/data/installs/aqua-google-yamlfmt/0.17.0/yamlfmt` |

SHA-256 values for every prepared executable and maintained input are in
`/tmp/score-m7-mise/result.json`. The source snapshot staged for the
provisioner was 22 maintained catalog, owner, and lock files (70,716 bytes);
it did not include `experiments/` or a worktree copy. The fresh data and bin
directories were `/tmp/score-m7-mise/runtime/data` and
`/tmp/score-m7-mise/runtime/bin`. No M5 or M6 installed-tool payload was
copied into that prefix.

## Reproduction commands

The base image was the already cached
`score-tooling-reference:final-arm64`, image ID
`sha256:b36448960057f54745f841561338487c5e9e2128526113c24b4861a7cf0f065a`.
It reports Ubuntu 24.04.5, `aarch64`, and Python 3.12.3. The Docker host is
amd64 and used QEMU user emulation for ARM64 containers; this is not a claim of
physical ARM hardware execution. The provisioner task had network access for
locked artifacts. The runtime and wheel consumer tasks used `--network none`,
`uid=1000:1000`, and read-only root filesystems.

Bootstrap mise into its own prefix, then invoke the maintained provisioner for
both selected environments:

```console
docker exec score-m7-mise-arm64-provision /bin/bash -lc 'set -eu; bash /tmp/score-m7-mise/source/tools/internal/mise/bootstrap.sh /tmp/score-m7-mise/runtime/mise; /tmp/score-m7-mise/runtime/mise/mise --version'
docker exec score-m7-mise-arm64-provision /bin/bash -lc 'set -eu; python3 /tmp/score-m7-mise/source/tools/internal/mise/provision.py s-core-local --owner-root /tmp/score-m7-mise/source/tools/mise --data-dir /tmp/score-m7-mise/runtime/data --bin-dir /tmp/score-m7-mise/runtime/bin --mise /tmp/score-m7-mise/runtime/mise/mise'
docker exec score-m7-mise-arm64-provision /bin/bash -lc 'set -eu; python3 /tmp/score-m7-mise/source/tools/internal/mise/provision.py bazel-feature --owner-root /tmp/score-m7-mise/source/tools/mise --data-dir /tmp/score-m7-mise/runtime/data --bin-dir /tmp/score-m7-mise/runtime/bin --mise /tmp/score-m7-mise/runtime/mise/mise'
```

The bootstrap checksum passed and returned mise `2026.10.24 linux-arm64`.
The provisioner installed 7 base native tools, 4 PyPI tools through the
maintained pinned-uv configuration, then Bazelisk, Buildifier and Starpls.

The ordinary dependency wheel was built and checked locally with the
maintained package generator and explicit local release identity:

```console
python3 tools/internal/mise/python_package.py build \
  --output /tmp/score-m7-mise/dependency-release \
  --version 0.6.1 \
  --package-name score-mise-dependencies \
  --uv /tmp/score-m5-mise/provision-bin/uv
python3 tools/internal/mise/python_package.py check \
  /tmp/score-m7-mise/dependency-release
```

The resulting `score_mise_dependencies-0.6.1-py3-none-any.whl` SHA-256 is
`2518871b2c815a56480f1f35c370eca02af52e67e0bed606efeec4fcb98b73a1`. This
package identity was selected only for this local evidence run; no public
release identity, host, or credentials were selected, and no publishing was
attempted.

The ARM uvx cache was populated as uid 1000 in the networked provision task
using the local wheel, then consumed offline:

```console
docker exec --user 1000:1000 -e HOME=/home/vscode -e PATH=/tmp/score-m7-mise/runtime/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin -e UV_CACHE_DIR=/tmp/score-m7-mise/runtime/uv-cache -e UV_PYTHON=/usr/bin/python3 -e UV_PYTHON_PREFERENCE=only-system score-m7-mise-arm64-provision /bin/bash -c '/tmp/score-m7-mise/runtime/bin/uvx --from "score-mise-dependencies[ruff] @ file:///tmp/score-m7-mise/runtime/release/score_mise_dependencies-0.6.1-py3-none-any.whl" ruff --version'
docker exec score-m7-mise-arm64-runtime /tmp/score-m7-mise/probes/selected-versions.sh
docker exec score-m7-mise-arm64-runtime /tmp/score-m7-mise/probes/execute-behaviors.sh
docker exec score-m7-mise-arm64-consumer /bin/bash -lc 'set -eu; id; uname -m; uv lock --offline; uv sync --offline; uv run --offline --no-sync ruff --version'
```

The runtime version sweep verified that each exposed command resolved inside
the fresh M7 install prefix. Direct and strict prepared `run-tool` invocations
matched for Ruff and pre-commit; poison `mise` and `bazel` commands were not
called. Offline behavior probes passed: local-wheel `uvx` ran Ruff 0.11.13;
Ruff caught the deliberate undefined name (`F821`, exit 1); one pytest fixture
passed; pre-commit accepted its fixture config; basedpyright reported zero
errors; Actionlint, ShellCheck, and Buildifier accepted their fixtures; and
codespell caught the deliberate `teh` typo (exit 65). The separate offline uv
consumer locked and synced the local wheel and ran Ruff 0.11.13.

### Bazelisk boundary

The pinned Bazelisk 1.27.0 binary was freshly prepared and executed in the
offline runtime. Its usual `--version` behavior tries to resolve the Bazel
version; the standalone `bazeliskVersion` subcommand is newer than this
selected pin. The safety probe instead set
`USE_BAZEL_FALLBACK_VERSION=error:m7-prepared-no-bazel-call` and invoked
`bazelisk --version`. It exited 1 with `not allowed to use fallback version`
and did not download or run Bazel. Attempts to obtain a self-version output in
the offline container were stopped after they remained in the resolver. Thus
binary execution and the no-Bazel boundary are evidenced, while a self-version
string for Bazelisk is unavailable without changing the pin or allowing Bazel
resolution.

## macOS ARM configuration review

Static lock/config review found Linux-and-macOS ARM URLs plus SHA-256 entries
for all nine records in `mise.native.lock` and the Starpls record in
`mise.published.lock`. `bootstrap.sh` includes the `Darwin:arm64` case and
checksum for the pinned mise bootstrap. The four PyPI tools use generic
Python/uv resolution and do not carry per-platform asset URLs in the mise
owner file. This is configuration inspection only: no macOS ARM tool was
installed or executed.

## Maintenance ledger

| Responsibility | Maintained owner / recurring work |
| --- | --- |
| Selection and exact pins | `tools/environments.json` selects commands; `tools/mise/*.toml` owns backend/version configuration; mise lock files and `tools/lockfiles/*.lock.json` carry artifacts. Keep each pin in one owner source. |
| Platform installation | `tools/internal/mise/bootstrap.sh` supplies mise for supported host platforms. `tools/internal/mise/provision.py` runs the selected environment owners and reconciles only selected direct commands into the prepared bin directory. |
| Prepared execution | `tools/run-tool` keeps strict direct host execution and the existing Bazel fallback. M7 exercised strict direct calls with manager/Bazel poison markers absent. |
| Python compatibility and ordinary release | `tools/internal/mise/refresh.py` exports current owners to compatibility outputs. `tools/internal/mise/python_package.py` builds and checks a normal dependency wheel from those owners. Each release operator supplies an explicit version and package identity and decides the future host; no public identity or host is selected here. |
| One-time M7 evidence | Create a fresh target-platform prefix, provision selected owners from maintained APIs, fingerprint outputs, and run non-root offline checks. Review other platform configuration separately; this run reviewed macOS ARM without executing it. |
| Recurring platform maintenance | Keep artifact locks and package extras synchronized with the single owner sources, then repeat fresh-prefix execution on supported platforms. Treat platform gaps as explicit policy decisions; do not silently omit a selected tool. |

## Focused checks and limits

`python3 tools/internal/mise/refresh.py --check` passed with
`Owner locks and compatibility outputs are current`. `git diff --check`
passed. No maintained source code was changed for M7; the only M7 candidate
addition is this evidence document. Full raw logs, probe scripts, the fresh
prefix and `result.json` are under `/tmp/score-m7-mise/` for root archiving.

The host used network access only for checksum-pinned setup, PyPI resolution,
and warming the uvx/consumer caches. The final ARM runtime and consumer checks
had no network. Root controls the larger cross-candidate gates and shared
comparison archive. No image build, commit, push, publication, or candidate
winner decision was made by this worker.
