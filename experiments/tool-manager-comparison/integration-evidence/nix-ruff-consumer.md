<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

Ruff consumer parity passed using the existing M6 wheel under `/tmp/score-m6-nix/ruff-consumer`. Host `uv` and `uvx` were 0.13.6; both `uv run ruff --version` and `uvx --with ...[ruff] --from ruff ruff --version` returned `ruff 0.17.2`. The wheel metadata and `uv.lock` both assert the owner pin `ruff==0.17.2`.

Wheel identity: `score-devcontainer-nix-candidate==0.0.0+m6.nix`, SHA-256 `eb5f63657cf15936ede2dda390e01389b79b3dbefe94a9ddcb14382b4445bbd0`. The existing UV cache stayed at 2.0 MiB. No source code or images were changed.

Recorded the commands and results in [README-m6.md](/home/alex/git/etas-contrib/score_devcontainer-eval-nix/experiments/tool-manager-nix/reference/README-m6.md) and the [final report](/tmp/score-m6-nix/final.md).
