<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

Updated the Aqua candidate’s [Dev Container config](/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/.devcontainer/devcontainer.json) to explicitly use `remoteUser: node` and put `/home/node/.local/share/score-tools/bin` on `remoteEnv.PATH`. That matches the prefix post-create provisions, so fresh terminals can find the prepared executables directly without a manager wrapper or duplicated tool versions.

The config assertions passed; an interactive Bash PATH check resolved cached `uv` and `uvx` 0.13.6, and `git diff --check` passed. I documented the lifecycle failure, fix, and exact checks in [README-m6.md](/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/experiments/tool-manager-aqua/reference/README-m6.md:84) and updated the [/tmp readiness report](/tmp/score-m6-aqua/final.md:1).

The real post-up terminal retry remains root-owned and is still pending; I did not run it or any full build. No commit or push was made.
