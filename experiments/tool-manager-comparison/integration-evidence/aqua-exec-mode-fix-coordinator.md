<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

Fixed [provision_image_tools.sh](/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/tools/internal/devcontainer/provision_image_tools.sh) to mode `100755`; its contents are unchanged. Both Dockerfiles invoke it directly. Nearby direct entrypoints were already executable, and Python helpers are called through `python3`.

Both shebang pre-commit hooks, `bash -n`, ShellCheck, and whitespace checks passed. Updated [README-m6.md](/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/experiments/tool-manager-aqua/reference/README-m6.md) and the `/tmp/score-m6-aqua` handoff. All three Node lifecycle gates and the Nix/Mise gates passed; the Aqua image retry remains root-owned. I did not run a full build or commit changes.
