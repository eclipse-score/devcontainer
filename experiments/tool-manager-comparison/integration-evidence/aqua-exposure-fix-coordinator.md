<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

**Aqua source is ready for root’s fresh retry.** The readiness marker is [aqua.exposure-fix.last.md](/tmp/score-m6-aqua/aqua.exposure-fix.last.md).

The failure came from Aqua `cp` exposing an unselected `gh` from the published `uv` copy. It shadowed APT’s selected `gh` on `PATH`. The feature assertion remains the original unqualified `gh --version` check. The provisioner now stages Aqua output privately, requests the owner-selected native commands (including `uvx`), verifies each selected executable exists, and promotes only those files. The existing foreign-command guard and APM runtime copy remain intact.

**Checks passed:** 13 focused Python tests, targeted Ruff and format checks, Python compilation, shell syntax/ShellCheck, and executable-mode audit. Regression coverage verifies extra `gh` is not exposed, a foreign `gh` sentinel survives, missing selected output fails, and deselection retires an owned command.

The actual cached-manager smoke used fresh prefix `/tmp/score-m6-aqua/prefix-exposure-fix`; its final `bin` matched the current repository selection, contained no `gh`, and its nine commands passed version checks. A copied-owner reprovision retired `buildifier`. The real published/APM profile was not separately rerun; that extra-output case is covered by the regression double and root owns the full image retry. The prefix is 125 MiB.

Details are in [provision_host_tools.py](/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/tools/internal/devcontainer/provision_host_tools.py:81), [test_provision_host_tools.py](/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/tools/tests/test_provision_host_tools.py:227), and [README-m6.md](/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/experiments/tool-manager-aqua/reference/README-m6.md:136). No image build or commit was made.
