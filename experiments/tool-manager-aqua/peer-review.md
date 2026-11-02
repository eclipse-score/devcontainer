<!--
SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Cross-review: aqua, mise and Nix

Date: 2026-10-31. **Phase 1: inspection and cross-agent discussion only.** No new
integration tests, production edits or architecture adoption in this phase.

Reviewed the current primary `docs/tooling-decision-record.md` (including its
provisional mise recommendation), all three experiment reports, mise's configs,
lock/export/harness, and Nix's flake, export and smoke procedure. Sibling
worktrees were read-only. The original probes share requirements but do not have
equal test depth; this review separates evidence strength from capability.

## Findings that change the comparison

1. **One manager is not yet a proven reduction in our maintenance.** mise uses
   aqua recipes for native packages and uv for Python. Its real tested convenience
   is shared install ordering, config environments, `use`/`unuse`, and bin-path
   discovery. aqua plus a standard requirements file uses two native backends
   explicitly. Both satisfy the permitted multi-file authoring model. The current
   evidence does not establish that a small `aqua cp` plus `uv venv`/`uv pip install`
   sequence costs materially more than mise's profile/lock setup and installation
   path integration. The mise agent agrees with this qualification.
2. **The exporters face similar native layout knowledge.** Both aqua and mise
   examples hardcode Ruff's archive-to-executable layout. aqua executed its
   generated native Bazel target; mise checked metadata equivalence instead.
   That is unequal evidence, not proof that mise cannot deliver the same artifact.
   Neither prototype is a complete generic exporter. Comparing their line counts
   would also be misleading: mise's example additionally exports Python metadata.
3. **Nix's package ecosystem is both capability and integration responsibility.**
   Its flake already owns environments and delegates dependencies to Nixpkgs,
   rather than requiring our handwritten transitive inventory. The store closure
   is not a disqualifying defect: it is a legitimate installation output which
   can be copied/retained for container execution. Direct copying of one ELF
   failing demonstrates an invalid export method, not a failed candidate.
4. **Historical versions and byte identity are not common acceptance tests.**
   Nix's packaged Ruff version differs, aqua uses musl, and mise uses GNU. The
   confirmed guarantee is equal tool versions across each selected release's
   delivery paths. None of these differences alone violates it. Package patches
   can matter functionally, but identical artifacts were explicitly not required.
5. **The consumer interface is still a choice.** A release checkout plus uv,
   `mise exec`, and `nix run` are all plausible no-Container/no-Bazel workflows.
   None currently proves the complete selected-release host contract from an
   unrelated checkout with hostile PATH/config and unchanged cwd/args/exit.
   A uv-only Git-package launcher is additional integration for every candidate,
   not an adopted requirement that automatically favors aqua.

## Weaknesses in my aqua experiment

- The Python pin change and native Ruff version change were executed, but adding
  a new package only generated its declaration; deletion/physical cleanup and a
  real two-environment workflow were described rather than comprehensively run.
  Do not treat these as equal evidence to Nix's selection evaluation or mise's
  executed overlay. Tag filtering is a native mechanism, not yet proof of our
  complete desired environment workflow.
- The fixed Python venv ran locally as the current user. Neither its permissions
  for another user nor a stable final image prefix was validated. The same gap
  exists for mise's bin-path proof. Nix's Docker execution is not automatically
  a non-root Ubuntu-container integration proof either.
- The exported Python requirements were not wired into existing Bazel Python
  targets. My native Bazel test must not imply Python Bazel completion.
- `UV_OFFLINE=true` on one prepared cache is narrower than Nix's disconnected
  network proof. Conversely, the stronger Nix test establishes only the prepared
  tools/local fixture, not all future hooks or ten-year archival.
- `aqua install --tags` only restricts eager installation and leaves lazy proxies
  for other configured packages. For fixed image membership, `aqua cp --tags`
  is the appropriate tested primitive. This limitation belongs in the workflow,
  not as an argument against any multi-backend architecture.
- Native aqua lacks a PyPI backend; uv is a real companion, with bootstrap and
  integration work to own. Using a normal requirements file is compliant, but
  that fact alone does not prove our two-backend workflow simpler than mise.
- The pinned aqua registry, uv verification helper downloads and generated hashes
  have their own update/retention implications. Counting only the two direct
  tool pins hides backend policy, just as treating mise's backend execution as
  effortless would hide its policy.

## Approaches worth reusing from the other probes

- From **mise**: one explicit command to compose known config environments;
  discover bin paths through native APIs rather than guessing installation
  directories; keep native artifact locking separate from version-only Python
  policy when a common lock would introduce extra runtime decisions.
- From **Nix**: export evaluated metadata with native package APIs; describe
  direct selections and let the backend own transitive resolution; keep the
  runtime closure instead of pretending a package's main executable is always
  portable; distinguish a package-set update from an independent tool update.
- For **all**: the final product adapter must select a trusted release/config
  deliberately while preserving the caller's directory. An experimental harness
  that changes into its own config directory is not that adapter.

## Three agreed common follow-up checks

These specify observable outcomes, not identical config syntax or mechanisms.
The mise and Nix agents both agreed to these checks through direct discussion.
The parent must approve the shared Phase-2 protocol before execution.

### 1. Direct-tool update and environment selection

Change one requested tool to another available released version, keeping the
other directly selected tool at its previous version. Demonstrate the chosen
package membership for two environment selections and expose the exact authored
and generated diff. Versions and membership have one maintained owner; derived
metadata does not introduce a second hand-maintained pin.

For Nix, another published Nixpkgs input and selecting one package from it is a
valid method. Do not demand an arbitrary historical recipe, an unchanged complete
transitive closure, or direct per-package version-string editing. Report the
extra input/snapshot-selection cost honestly. For aqua, requirements includes and
package tags/imports are valid; for mise, native environment configs are valid.
Deleting a request need not uninstall a cached package, but the intended next
fresh environment must have the right membership.

### 2. Selected-release host execution

From a temporary consumer checkout, invoke the selected release's tool through
the proposed public host interface without Container or Bazel. Place a wrong
version on consumer PATH and an unrelated conflicting tool-manager config in
that checkout. Observe the selected version, caller cwd, argument boundaries and
an intentional nonzero exit status being preserved. The runner must not silently
use the wrong local tool/config.

uv-only and manager-based surfaces are equally valid candidates. Record all
bootstrap steps, required installed programs, and product adapter code. A shared
published `uvx` packaging contract is not imposed before U5 is decided. An
unsupported command must not silently become arbitrary PATH execution in strict
mode. Container mode remains trusted and needs no per-call version validation.

### 3. Prepared direct execution under another user

Prepare the two tools under an intended stable install/image filesystem layout,
then run them directly as a non-root user without invoking the manager or allowing
runtime downloads. Use the existing small functional fixtures; show versions,
access to supporting runtime files and observable command results. A read-only
prepared closure, fixed venv or native executable copy are all valid outputs.

This need not rebuild the full S-CORE production image. A minimal controlled
runtime/image can expose the integration issue. Nix closures are legitimate;
copying only binaries is not imposed. A tool-manager CLI may exist in the
filesystem but should not be required to execute already provisioned tools.

## Evidence already sufficient: do not inflate tests

- All three candidates already start tools, exercise Ruff's failing fixture and
  run a local pre-commit system hook. Do not expand to arbitrary real hook graphs
  or full downstream builds just for comparison parity.
- All three have credible macOS ARM metadata/evaluation evidence and no actual
  Mac execution. Record the common gap; do not pretend another Linux download or
  evaluation makes one candidate proven on macOS.
- aqua's real native Bazel run and mise's exact generated metadata comparison are
  enough to establish a plausible bounded portable bridge. Nix exports versions
  but still needs release-asset/hash/layout integration. That is an explicit cost
  difference; no complex closure-packaging framework is needed to make it match.
- Existing star/activity snapshots are adequate context, not a reason for more
  adoption research or a capability score.
- Prepared offline evidence is qualified adequately. A shared non-root direct
  execution check may reuse existing prepared outputs; there is no need for a
  complete cross-candidate air-gap/archival certification exercise now.
- Legacy APT prefix flags, CodeQL pruning and every inherited image helper remain
  outside this candidate probe. They must not become accidental knockout tests.

## Open question and provisional judgment

The three common checks are agreed; no substantive criteria dispute remains.
The open question is whether mise's useful shared orchestration actually removes
enough maintained lifecycle work to outweigh its extra manager/profile/lock
policy, compared with two explicit standard backend configs. A priori neither
configuration count nor one-manager branding answers that question.

No new integration was started during this cross-review. The first-round
recommendation should remain a hypothesis until the common Phase-2 observations
make that tradeoff visible.
