<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# M6 integration gate harness

The harness keeps M6 integration evidence isolated from the candidate
worktrees. Source defaults point to
`/home/alex/git/etas-contrib/score_devcontainer-eval-{mise,aqua,nix}`. Mise and
Aqua require their lifecycle-fix readiness reports; Nix's published build
requires the validated M6 release report before source is read.

## Generic Node lifecycle

The `lifecycle` gate snapshots one stable candidate at a time under
`/tmp/score-m6-gates/`. It omits only the candidate root `.git`, known
generated caches/output (`.venv`, Python caches, `node_modules`, root Bazel
output symlinks), and prepared Nix runtime/store/activation/release payloads.
It also omits the Nix candidate's generated historical
`experiments/tool-manager-nix/reference/evidence` and `out` payloads; those
alone were 4.5 GiB and are not read by the root lifecycle.
Other tracked and untracked source and local inputs are copied. It initializes
a task-local `.git` so `pre-commit install` can only change the temporary hook.

It runs the current root `.devcontainer/devcontainer.json` with
`devcontainer up`: the generic Node image, Docker-in-Docker feature, and real
`postCreateCommand` all execute. After `up`, it starts a **new interactive
`bash -ic` shell** and records the actual user, `$HOME`, resolved paths, file
owners and versions for `uv`, `uvx`, `ruff`, and `pre-commit`. It also asserts
the copied `.git/hooks/pre-commit` exists and checks the nested Docker daemon
and Buildx builder with `docker info` and `docker buildx inspect --bootstrap`.
This catches terminal PATH/HOME behavior that a successful post-create shell
alone does not prove.

Before `up`, the runner snapshots only Docker volume names (not volume
descriptions). During cleanup it inspects mounts only on containers carrying
the run's exact `score-m6-gates.run` label, journals each mounted volume's
pre-run existence, removes those task containers, restores root-owned files in
the exact mounted task workspace to the host owner before deleting it, preserves
pre-existing volumes (including an existing shared `vscode` volume), and removes only
previously absent volumes mounted by those task containers. It removes only
image tags observed from the disposable workspace build. Docker base and
feature layers remain in shared storage; no prune is used.

## Fresh published image gate

The `published` gate builds the actual full `src/s-core-devcontainer` config
fresh for `linux/amd64`, then runs the existing
`src/s-core-devcontainer/test-project/test.sh` from the rendered Dev Containers
feature build as `vscode` in `bash -lc`. The test command derives `HOME` from
the effective user's passwd entry and verifies it, so normal `/etc/profile`
and `/etc/profile.d` exports are loaded without setting feature variables by
the harness. It uses a task-only `score-m6-gates-*`
`docker-container` Buildx builder and `type=cacheonly`; the result is not loaded
into Docker or launched. The wrapper removes `--target`, cache output, and
load/push options as needed to make the appended feature-test command the last
build step, and forces `--no-cache` plus cache-only output.

Nix uses its current `scripts/build.sh --amd64 <task-tag>` entrypoint with the
validated `/tmp/score-m6-nix/release-amd64` and artifacts root
`/tmp/score-m6-nix`. That script validates the release against current owners
via `sync.py --check --release` before staging. A task
`devcontainer` shim intercepts its build call, removes the shared `--cache-from`
input, and adds the task Docker wrapper, `--no-cache`, and cache-only output.
`TMPDIR` points inside `/tmp/score-m6-gates`; the Nix script stages one
build-context copy there and deletes it on exit. It does not copy the full
candidate worktree first or modify the candidate. If the retained M5 release is
stale, the gate fails visibly and requires root coordination; it does not skip
the owner/release check.

Each published build has live free-space monitoring. The process group receives
SIGINT when free space falls below the configured stop limit (1.5 GiB by default),
then SIGTERM and SIGKILL if it does not exit within bounded intervals. Its
task-only builder is removed afterward to reclaim that build's cache. The
normal default/shared builder is never selected, removed, or changed.

## Disk budget and cleanup

- Lifecycle preflight requires **4 GiB free**, checked before and after the
  source snapshot. The root Node image was already cached when this revision
  began; root reported 9.4 GiB free.
- A single candidate snapshot, container, and its generated image tag exist at
  a time. The snapshot is removed after the gate unless `--keep-workspace` is
  requested. Small logs, `result.json`, a volume baseline count, and the
  task-container volume journal remain under `/tmp/score-m6-gates/`.
- Published builds also start with the 4 GiB preflight and cancel live if free
  space falls below 1.5 GiB by default. This is a lower reserve, not a claim that
  every full image will fit; cancellation is bounded and task builder cleanup
  is attempted immediately.
- Cleanup targets exact run-labeled containers, task-mounted volumes proven
  absent before the run, exact image tags recorded by the wrapper, and the
  uniquely named Buildx builder. It never runs a shared prune or enumerates
  unrelated image/build descriptions.

## Commands

Use gate-specific readiness reports before each source snapshot. Run the current
authorized gates serially in this order:

```sh
python3 experiments/tool-manager-comparison/integration-gates/gate.py run --candidate nix --gate published --min-free-gib 4 --build-stop-free-gib 1.5 --disk-check-interval 2
python3 experiments/tool-manager-comparison/integration-gates/gate.py run --candidate mise --gate lifecycle --min-free-gib 4
python3 experiments/tool-manager-comparison/integration-gates/gate.py run --candidate mise --gate published --min-free-gib 4 --build-stop-free-gib 1.5 --disk-check-interval 2
python3 experiments/tool-manager-comparison/integration-gates/gate.py run --candidate aqua --gate lifecycle --min-free-gib 4
python3 experiments/tool-manager-comparison/integration-gates/gate.py run --candidate aqua --gate published --min-free-gib 4 --build-stop-free-gib 1.5 --disk-check-interval 2
```

The roots may also be stated explicitly:

```sh
python3 experiments/tool-manager-comparison/integration-gates/gate.py run --candidate nix --source /home/alex/git/etas-contrib/score_devcontainer-eval-nix --gate lifecycle
python3 experiments/tool-manager-comparison/integration-gates/gate.py run --candidate mise --source /home/alex/git/etas-contrib/score_devcontainer-eval-mise --gate lifecycle
python3 experiments/tool-manager-comparison/integration-gates/gate.py run --candidate aqua --source /home/alex/git/etas-contrib/score_devcontainer-eval-aqua --gate lifecycle
```

Do not rerun the already-passing Nix lifecycle unless its source changes. The
published gate proves a fresh amd64 build and build-stage feature-test run; it
does not prove a launched runtime image. `run-all` defaults to both gate
families, so use the individual commands above to preserve the required order.
