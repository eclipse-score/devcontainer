<!-- SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# M8 Nix: complete local release and user update

The maintained workflow produced local `score-devcontainer-nix-candidate`
releases **0.8.0 / Ruff 0.17.2** and **0.8.1 / Ruff 0.14.6**. All six M8
acceptance boundaries passed. Worktree owner pins remain unchanged; only the
isolated B owner selects historical Ruff. No package identity/hosting decision,
publication, image build, ARM/macOS execution, or adoption claim is made.

The supported maintainer/user instructions are now in
[tools/internal/nix/README.md](/home/alex/git/etas-contrib/score_devcontainer-eval-nix/tools/internal/nix/README.md).
Raw commands and outputs are under `/tmp/score-m8-nix`; compact handoff files are
`result.json` and `final.md`. Nothing in the production workflow reads/writes
experimental sources.

## Owners, releases and generated outputs

Small `source-a` and `source-b` copies contain current maintained `tools/` plus
only the Bazel, inventory and Dev Container configuration needed by those APIs.
They contain no old runtime trees or historical generators. `stage.py` records
the exact copied files. B adds `ruffPkgs` at revision
`b6018f87da91d19d0ab4cf979885689b469cdd41`, adds that outputs argument and selects
only `(import ruffPkgs { inherit system; }).ruff`. The main nixpkgs input remains
`1c89083e451e891152365b799595cf7790a43325`.
This revision came from prior round-three knowledge, not automatic arbitrary
version discovery. No second authored Ruff version pin was introduced.

Exact owner locking commands:

```sh
python3 /tmp/score-m8-nix/edit-owner.py
docker cp /tmp/score-m8-nix/source-b/tools/nix score-eval-nix-m5-agent:/tmp/score-m8-lock-owner
docker exec score-eval-nix-m5-agent nix --extra-experimental-features 'nix-command flakes' \
  flake lock --offline path:/tmp/score-m8-lock-owner
docker cp score-eval-nix-m5-agent:/tmp/score-m8-lock-owner/flake.lock \
  /tmp/score-m8-nix/source-b/tools/nix/flake.lock
python3 /tmp/score-m8-nix/source-b/tools/internal/nix/sync.py --check
# exit 1: tools/lockfiles/ruff.lock.json is stale
python3 /tmp/score-m8-nix/source-b/tools/internal/nix/sync.py
python3 /tmp/score-m8-nix/source-b/tools/internal/sync_readme.py
python3 /tmp/score-m8-nix/source-b/tools/internal/nix/sync.py --check
python3 /tmp/score-m8-nix/source-b/tools/internal/sync_readme.py --check
# both exit 0
```

`authored-owner.diff` records the exact flake/lock change. `generated.diff`
contains only Ruff's portable version, URLs/checksums, and the overview row.
All other 14 versions and both profile membership lists are equal. Locking's
`--offline` flag does not describe the full workflow: subsequent evaluation
fetched the historical source through cache.nixos.org. The source occupies
446 MiB; nine binary substitutes required 22.9 MiB downloaded / 83.6 MiB
unpacked. Two small profile derivations were assembled; Ruff was not compiled.

Initial maintained preparation commands:

```sh
python3 /tmp/score-m8-nix/source-a/tools/internal/nix/prepare.py /tmp/score-m8-nix/release-a \
  --release-version 0.8.0 --package-name score-devcontainer-nix-candidate \
  --reuse-native-from /tmp/score-m6-nix/release-amd64
python3 /tmp/score-m8-nix/source-b/tools/internal/nix/prepare.py /tmp/score-m8-nix/release-b \
  --release-version 0.8.1 --package-name score-devcontainer-nix-candidate \
  --reuse-native-from /tmp/score-m8-nix/release-a
```

A reused 183 store objects without transferring payload. B reused 180 and
transferred 11 missing objects (including both new profiles). The final API
removed an obsolete Dockerfile export; the first directories were renamed
`release-{a,b}-before-cleanup` and final releases were prepared at the original
paths with `--reuse-native-from` their corresponding pre-cleanup directories.
Both final release bindings, pyprojects and activation scripts are byte-identical
to the tested versions. Their obsolete Dockerfiles are absent. Final logs are
`prepare-a-final.log` and `prepare-b-final.log`.

Final owner checks:

```sh
python3 /tmp/score-m8-nix/release-check.py
python3 /tmp/score-m8-nix/closure-check.py
python3 tools/internal/nix/sync.py --check \
  --release /tmp/score-m8-nix/release-a --system x86_64-linux
python3 tools/internal/sync_readme.py --check
```

A against A and B against B exit 0. A against B exits 1, rejecting release
versions, package metadata and owner snapshots. `closure-check.json` confirms
all 183 A / 191 B exported store objects and both bundles match current owner
evaluation. The unchanged actual worktree also accepts A. Worktree flake/lock
SHA-256 values still equal the recorded M7 hashes.

## Same independent ordinary Python consumer

`python3 /tmp/score-m8-nix/consumer-check.py` built both ordinary wheels using
`uv build --wheel --no-sources --out-dir /tmp/score-m8-nix/handoff RELEASE` after
`package.py check RELEASE`. `consumer-commands.json` records exact argv, cwd,
exit/stdout/stderr for every operation. Consumer Python is `/usr/bin/python3`
3.12; uv and uvx are the already available ordinary host 0.13.6 executables.
The project has no producer, Nix, Bazel, experimental-source or SCORE-wrapper
requirement.

In the same `/tmp/score-m8-nix/consumer` project, for each version 0.8.0 then
0.8.1, the actual commands were:

```sh
/tmp/score-m5-mise/host-bin/uv add --find-links /tmp/score-m8-nix/handoff \
  'score-devcontainer-nix-candidate[ruff]==VERSION'
/tmp/score-m5-mise/host-bin/uv lock --find-links /tmp/score-m8-nix/handoff
/tmp/score-m5-mise/host-bin/uv sync --find-links /tmp/score-m8-nix/handoff
/tmp/score-m5-mise/host-bin/uv run --no-sync ruff --version
/tmp/score-m5-mise/host-bin/uv run --no-sync ruff check --no-cache 'bad input.py'
/tmp/score-m5-mise/host-bin/uvx --find-links /tmp/score-m8-nix/handoff \
  --with 'score-devcontainer-nix-candidate[ruff]==VERSION' --from ruff ruff --version
/tmp/score-m5-mise/host-bin/uvx --find-links /tmp/score-m8-nix/handoff \
  --with 'score-devcontainer-nix-candidate[ruff]==VERSION' --from ruff ruff \
  check --no-cache 'bad input.py'
```

Both paths reported Ruff 0.17.2 for A and 0.14.6 for B. All four negative
invocations returned F401 / exit 1 for `import os`. `consumer-a.toml` and
`consumer-b.toml` differ only in facade `==0.8.0` → `==0.8.1`; no Ruff pin is
copied into that project. `uv-a.lock` and `uv-b.lock` resolve Ruff from each
wheel's exact `Requires-Dist`, captured in `wheel-{a,b}-METADATA.txt`.

| Wheel | SHA-256 |
| --- | --- |
| `score_devcontainer_nix_candidate-0.8.0-py3-none-any.whl` | `301ea5c2fe6ccd982aa88525c17613e44402f5018332cffca0016f68f2d79615` |
| `score_devcontainer_nix_candidate-0.8.1-py3-none-any.whl` | `efe7e3d95573dce1e6dd4557a2bd366a6d537c56d71615ccc0899a3442b48499` |

## Same native user profile and public Bazel interface

`native-check.py` records all commands in `native-commands.json`. The existing
producer starts its Nix daemon, then executes the maintained installer as UID
65534 with HOME `/tmp/score-m8-home`, `NIX_REMOTE=daemon` and the same
`SCORE_NIX_PROFILE=/tmp/score-m8-home/profile`. The small maintained owner is
staged at `/tmp/score-m8-workspace/tools/nix` (first A, then B). The actual
provisioning entrypoint for both is:

```sh
docker exec --user 65534:65534 -e HOME=/tmp/score-m8-home -e NIX_REMOTE=daemon \
  -e SCORE_NIX_PROFILE=/tmp/score-m8-home/profile score-eval-nix-m5-agent \
  /nix/var/nix/profiles/default/bin/bash /tmp/score-m8-workspace/tools/nix/install-host.sh
```

A reports Ruff 0.17.2. After replacing the same staged owner and rerunning the
same installer, B reports 0.14.6. An unrelated user-installed fixed-store
`m8-unrelated` command remains; buildifier's resolved store path remains
identical and it reports 10.2.0. All profile generations belong to UID 65534.
The profile manifest before/after is captured. The installer uses Nix's
`profile upgrade --all`; independently updatable foreign flake entries would
also participate, so the unrelated-tool assertion concerns the fixed store
entry actually tested.

Updated direct calls and host-mode `run-tool --strict ruff` each returned
0.14.6 and F401/exit 1 with the spaced filename. PATH contained only a Bash
symlink and poison nix/bazel/ruff executables; no interception file was created.
Prepared calls did not resolve Nix or Bazel. Provisioning/network acquisition
was online; runtime checks were not put in a separate network namespace.
This is native amd64 execution, not QEMU or an ARM/macOS claim.

`bazel-check.py` used the cached Bazel 8.6.0 engine and existing M5 repository
cache. From `/tmp/score-m8-nix/source-b/tools`:

```sh
/home/alex/.cache/bazelisk/downloads/bazelbuild/bazel-8.6.0-linux-x86_64/bin/bazel \
  --ignore_all_rc_files --output_base=/tmp/score-m8-nix/bazel-output \
  run //tools:ruff --repository_cache=/tmp/score-m5-nix/bazel-repository-cache \
  --repo_env=UV_PYTHON_DOWNLOADS=never -- --version
# ruff 0.14.6, exit 0; same command with final args:
# -- check --no-cache 'bad input.py' => F401, exit 1
```

The relative filename proves caller cwd and spaced argv preservation through
the existing public alias. Generated amd64 archive URL/hash selection is in
`bazel-selection.json`; exact logs are in `bazel-commands.json`. Bazel is an
explicit compatibility consumer here, not an ordinary runtime dependency.

## Repairs, cleanup and responsibility ledger

| Frequency | Responsibility demonstrated / remaining |
| --- | --- |
| One time | Added `prepare.py --reuse-native-from`: recreate directories and symlinks, hardlink immutable files, transfer only missing store objects, never share metadata. Two new regression tests cover inode isolation/links and missing-object transfer. Seven existing cross-system tests still pass. |
| One time | Removed `tools/internal/nix/Dockerfile` and its export from `prepare.py`: it referenced an old comparison image and nonexistent `install.sh`; the current production build stages only the closure and activation script. Fresh final preparation and checks prove the release workflow does not need it. |
| One time | Added maintained release/user instructions and replaced the old required package-generation example with a link to the supported sequence. Existing package-only generation and pre-commit smoke helpers remain useful; no historical reports or compatibility paths were deleted. |
| Per version | Select/verify an available Nixpkgs snapshot; isolated-tool input may be needed. Edit owner, lock, reject drift, refresh portable digest/layout compatibility records and overview, review unrelated selections. GitHub asset metadata is a recurring external dependency. |
| Per release | Choose explicit release version/local identity; realize/probe profiles, prepare payload/metadata, validate owner binding, build wheels, test ordinary consumer update and selected runtime. |
| Per platform | Verify Nix substitutes, Python wheels and custom asset recipes, prepare target closure and execute it. M8 executes x86_64-linux only; M7 platform evidence remains historical. |
| Python user | Change only facade release requirement, lock/sync/run; uvx receives the same facade extra. Supply a local wheelhouse or hosting choice plus dependency index/cache. |
| Native user | Update the maintained owner checkout and rerun installer with the same dedicated user profile; manager work occurs at provisioning, prepared calls execute the selected store binary. |

Focused checks: **9 prepare unit tests passed**, Ruff source lint, Python compile
and `git diff --check` passed. A/B final owner/release checks, exact closure
checks, actual worktree current-owner check and overview check passed. No full
images or old unaffected suites were rerun. Expected failures were stale B
outputs, stale A release against B, and actual Ruff diagnostics; no unresolved
external failure remains in the requested M8 scope.

Resource accounting: A/B payloads share accepted immutable M6 files; metadata
has fresh inodes. `du -s -B1 M6_RELEASE /tmp/score-m8-nix` measured 455,647,232
additional host bytes for M8 after accounting for shared M6 inodes. Producer
additions include the 446 MiB historical snapshot and 83.6 MiB substitutes;
this snapshot reuse has a real disk cost. Global free space remained above
4 GiB (about 9 GiB at final checks). No global install/prune, image pull, full
closure duplicate, nested agent/CLI, commit/push or publication was performed.
The producer remains available, including the user profile for inspection.
