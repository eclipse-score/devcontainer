<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

The real same-prefix Aqua/uv reprovision **passed** using the maintained provisioner, actual Aqua 2.65.2, and uv 0.13.6 with the existing M5 caches. After removing only the copied owner’s repository tags for `buildifier` and `actionlint`, the CLI reported `retired_commands: ["buildifier"]`. The changed `actionlint` and unrelated sentinel remained intact.

Retained repository commands ran at their pinned versions: Bazelisk 1.27.0, pre-commit 4.7.0, Ruff 0.11.12, ShellCheck 0.10.0, uv/uvx 0.13.6, and yamlfmt 0.17.0. The M6 prefix was 116,326,719 bytes. No image, container, or full build was run, and no production source was changed in this turn.

Cross-profile repository/published sharing, Python alias sharing and retirement, and the additional symlink cases remain fixture-only. Exact commands, results, and that evidence boundary are recorded in [README-m6.md](/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/experiments/tool-manager-aqua/reference/README-m6.md:133) and [/tmp/score-m6-aqua/final.md](/tmp/score-m6-aqua/final.md:1). No commit or push was made.
