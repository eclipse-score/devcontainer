<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Nix M6 handoff

Implemented M6 in `/home/alex/git/etas-contrib/score_devcontainer-eval-nix` and recorded the detailed report at `experiments/tool-manager-nix/reference/README-m6.md`.

## Completed

- Added maintained `tools/internal/nix/package.py` generation and binding checks; `prepare.py` now requires `--release-version`, accepts a configurable `--package-name`, and records package identity, release version, and exact optional dependencies in `release.json`.
- `sync.py --check --release` validates the package binding against the current Nix versions/profile and generated PEP 621 metadata. The ordinary package generator, wheel check, and release exporter do not read or write `experiments/`.
- Added `python-package-check.py` for a normal local wheel/uv consumer and `profile-replacement-check.py` for real Nix profile membership changes.
- Kept existing public Bazel labels, `run-tool --strict` behavior, and fallback paths.
- Updated fresh build callers to pass an explicit release version. The local package identity used for M6 is `score-devcontainer-nix-candidate`; no public package identity or hosting was selected.

## Exact results

- `python3 tools/internal/nix/sync.py --check --release /tmp/score-m6-nix/package-source-v2 --system x86_64-linux` passed with `Stale outputs:` empty after evaluating all three declared systems. The release directory was metadata-only and reused M5 release metadata; no large closure was copied.
- The real Nix profile check passed: current profile had `buildifier 10.2.0`; after `nix profile upgrade --all`, `buildifier` was absent, `starpls v0.1.22` was present, and retained `ruff 0.17.2` still ran. Exact log: `/tmp/score-m6-nix/profile-replacement-check-final2.log`.
- The local wheel `score_devcontainer_nix_candidate-0.0.0+m6.nix-py3-none-any.whl` passed `uv add`, `uv lock`, `uv sync`, `uv run pre-commit --version`, and `uvx --with ... --from pre-commit pre-commit --version`; both execution paths printed `pre-commit 4.7.0`. Exact evidence: `/tmp/score-m6-nix/python-package-check-final3.log` and `/tmp/score-m6-nix/python-package-check-final3/commands.json`.
- Bazel `//tools:run_tool_test` and `//tools:python_tool_runner_test` both passed using the retained M5 Bazel caches.
- Ruff check, helper-script format checks, ShellCheck for `scripts/build.sh`, actionlint for both changed workflows, Python compilation, `bash -n`, and `git diff --check` passed.
- Root subsequently reported that the candidate image and feature suite and generic Node lifecycle passed. This worker did not run those gates. No hosted workflow or publication was run.

No commits, pushes, PRs, external messages, or publication were performed. All inherited dirty M1–M5 changes remain present.

## Latest M6 Ruff consumer parity

The existing producer-built M6 wheel was copied to
`/tmp/score-m6-nix/ruff-consumer/wheelhouse/`:
`score_devcontainer_nix_candidate-0.0.0+m6.nix-py3-none-any.whl`,
SHA-256 `eb5f63657cf15936ede2dda390e01389b79b3dbefe94a9ddcb14382b4445bbd0`.
Wheel identity is `score-devcontainer-nix-candidate==0.0.0+m6.nix`; its `ruff`
extra and the generated lock both pin owner version `ruff==0.17.2`.

Host `uv` and `uvx` were both 0.13.6. From `/tmp/score-m6-nix/ruff-consumer`:

```sh
/tmp/score-m5-mise/host-bin/uv init --bare --name score-m6-ruff-consumer
/tmp/score-m5-mise/host-bin/uv add --no-cache \
  'score-devcontainer-nix-candidate[ruff] @ file:///tmp/score-m6-nix/ruff-consumer/wheelhouse/score_devcontainer_nix_candidate-0.0.0%2Bm6.nix-py3-none-any.whl'
/tmp/score-m5-mise/host-bin/uv lock --no-cache
/tmp/score-m5-mise/host-bin/uv sync --no-cache
/tmp/score-m5-mise/host-bin/uv run --no-cache ruff --version
/tmp/score-m5-mise/host-bin/uvx --no-cache \
  --with 'score-devcontainer-nix-candidate[ruff] @ file:///tmp/score-m6-nix/ruff-consumer/wheelhouse/score_devcontainer_nix_candidate-0.0.0%2Bm6.nix-py3-none-any.whl' \
  --from ruff ruff --version
```

Both execution paths printed `ruff 0.17.2`. The pre-existing UV cache remained
2.0 MiB because the commands used `--no-cache`; the consumer output is about
25 MiB.
