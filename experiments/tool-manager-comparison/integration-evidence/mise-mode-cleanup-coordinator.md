<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

Set [refresh.py](/home/alex/git/etas-contrib/score_devcontainer-eval-mise/tools/internal/mise/refresh.py) and [python_package.py](/home/alex/git/etas-contrib/score_devcontainer-eval-mise/tools/internal/mise/python_package.py) to mode `755`.

Audited 41 maintained shebang scripts across the tool, devcontainer, feature, scripts, and mise reference paths; all are `755`. Generated evidence and caches were excluded. Both focused pre-commit hooks passed against 102 maintained files:

- `check-shebang-scripts-are-executable`
- `check-executables-have-shebangs`

`git diff --check` passed. Nothing was staged, and no content was changed in this cleanup. The source is ready for root’s final mode fingerprints.
