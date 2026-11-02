<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

**Stable source is ready** in the aqua checkout. Both Dockerfiles now install distro `python3` in their existing CA-refresh APT step, before the Python-based image bootstrap runs. This adds no tool-version pin and invokes no old installer. The base already provides the other commands needed at that boundary.

The cached-base check confirmed Python was missing, then installed `ca-certificates` and `python3` in a disposable container. Python 3.12.3 started the Aqua bootstrap, host provisioner, and provider CLI; no tool payloads or image layers were built. Both Dockerfiles passed `docker buildx build --check`; shell syntax, ShellCheck, and whitespace checks passed.

The fix and exact evidence are in [README-m6.md](/home/alex/git/etas-contrib/score_devcontainer-eval-aqua/experiments/tool-manager-aqua/reference/README-m6.md:49). The readiness report and root-owned gate commands are in [final.md](/tmp/score-m6-aqua/final.md:1). Full image, Node lifecycle, and Nix gates remain with root. No commits or publication were made.
