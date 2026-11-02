<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

Prepared the full amd64 M6 release at `/tmp/score-m6-nix/release-amd64`. Its package binding and `pyproject.toml` were generated through `package.py` with identity `score-devcontainer-nix-candidate` at `0.0.0+m6.nix`; the retained M5 release was left untouched.

Validation passed: `sync.py --check --release` reported no stale outputs. The closure verifier matched both bundle paths and all 183 store paths to the current Nix owner. It confirmed 32,362 regular payload files are hardlinked to M5 and the M6 metadata has separate inodes, avoiding another 1.4 GiB copy.

The image gate can use the prepared release with:

```sh
SCORE_M5_NIX_ARTIFACTS=/tmp/score-m6-nix \
SCORE_NIX_PREPARED_RELEASE=/tmp/score-m6-nix/release-amd64 \
SCORE_NIX_IMAGE_REPOSITORY=score-nix-m6 \
SCORE_NIX_KEEP_BUILD_CONTEXT=1 \
scripts/build.sh --amd64 m6-image
```

I did not build an image. Updated [README-m6.md](</home/alex/git/etas-contrib/score_devcontainer-eval-nix/experiments/tool-manager-nix/reference/README-m6.md>) with the artifact details and verification results.
