<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

## Fix

The lifecycle log shows native mise installation succeeded, then `pypi:pre-commit@4.7.0` fell back to pipx. The provisioner had put uv’s reported install root on PATH, but the executable is nested below it. The cached host setup had masked that gap.

In [provision.py](/home/alex/git/etas-contrib/score_devcontainer-eval-mise/tools/internal/mise/provision.py:384), provisioning now resolves the pinned uv executable, adds its containing directory to PATH, and sets `MISE_PYPI_UVX=true`. It fails before PyPI installation if mise cannot resolve the selected uv version. This follows mise’s requirement that uv be on PATH for its PyPI backend. [Mise PyPI backend documentation](https://mise.jdx.dev/dev-tools/backends/pypi.html)

The regression tests cover the nested install layout with an empty ambient PATH and failure when the pinned uv is missing. The fresh-data mise smoke installed `pypi:pre-commit@4.7.0` using uv and returned `pre-commit 4.7.0`.

## Checks and retry

The 11-test Python suite, Ruff check/format, `git diff --check`, and all four focused Bazel targets passed. The provisioner target ran; the other three were cached.

The clean root lifecycle retry remains pending. From the repository root, run:

```console
./scripts/build.sh --amd64 score-m6-mise
docker run --rm --entrypoint /bin/bash ghcr.io/eclipse-score/devcontainer:score-m6-mise-amd64 -lc 'uv --version && uvx --version && pre-commit --version && starpls version'
devcontainer up --workspace-folder "$PWD" --config .devcontainer/devcontainer.json
devcontainer exec --workspace-folder "$PWD" --config .devcontainer/devcontainer.json bash -lc 'uv --version && uvx --version && pre-commit --version && uvx --from "codespell==2.4.1" codespell --version'
```

The updated [M6 README](/home/alex/git/etas-contrib/score_devcontainer-eval-mise/experiments/tool-manager-mise/reference/README-m6.md:54) and `/tmp/score-m6-mise/final.md` record the failure, fix, smoke results, and maintenance ledger. Source is stable for the root retry; I did not run the image build or lifecycle retry, and made no commit or publication.
