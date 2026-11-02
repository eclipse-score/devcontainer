<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

The final Aqua retry **passed**. After reading the exposure-fix report, I verified that `test_default.sh` still uses the original unqualified `gh --version` assertion. The fresh amd64 cache-only build and full feature suite passed, including that assertion.

Result and log: [result.json](/tmp/score-m6-gates/aqua-published-20261102T012420Z-ee53ca4a/result.json) and [published-build.log](/tmp/score-m6-gates/aqua-published-20261102T012420Z-ee53ca4a/published-build.log). The exact builder, snapshot workspace, and task image tag are absent; disk returned to 13 GiB free. The earlier failed Aqua attempts remain preserved. No image was loaded, and I made no candidate or docs edits. Progress is recorded in [progress.md](/tmp/score-m6-gates/progress.md).
