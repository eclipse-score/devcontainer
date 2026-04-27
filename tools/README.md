<!--
*******************************************************************************
Copyright (c) 2026 Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0

SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
SPDX-License-Identifier: Apache-2.0
*******************************************************************************
-->

# Tooling Strategy: Reproducible CLI Tools Across Development Environments

> This document complements the general infrastructure direction defined in
> [DR-001 Infrastructure Design Decision](https://eclipse-score.github.io/score/main/design_decisions/DR-001-infra.html)
> and specifies how CLI tooling is provided across environments.

## Purpose

We provide selected CLI tools such as `actionlint` and `shellcheck` in a reproducible way across supported development environments.

The goal is simple:

- same tool versions
- same behavior
- same results

independent of how developers choose to work.

---

## Strategy

We support two ways to access the same tooling:

- **DevContainer**
- **Bazel via `rules_multitool`**

Both are supported intentionally.

Not all developers work the same way. Some prefer a fully managed environment, others prefer to stay on their host system. Both workflows exist in practice, and both need to produce identical results.

![Tooling architecture](arch.svg)

---

## Design Principle

> Reproducibility is required.
> The execution path is a developer choice.

This means:

- no reliance on system-installed tools
- no hidden dependencies
- no environment-specific behavior

---

## DevContainer

The DevContainer provides:

- a ready-to-use environment
- minimal setup effort
- predictable tooling

For many developers, this is the most straightforward option.

---

## Bazel-Based Tool Access

We additionally expose tools via Bazel using [`rules_multitool`](https://github.com/bazel-contrib/rules_multitool).

Example usage:
- `bazel run //tools:actionlint`
- `bazel run //tools:shellcheck`

This exists primarily to support workflows outside the DevContainer.

It allows:

- reproducible tool execution on the host
- consistent versions across platforms
- alignment with CI execution

At the same time, invoking standalone tools through a build system is not always the most ergonomic experience. The setup therefore focuses on making this path reliable rather than minimal.

---

## Why We Support Both

In practice:

- some developers use the DevContainer
- some developers do not
- some switch between both depending on the task

Relying on only one of these paths would either:

- reduce adoption (DevContainer-only), or
- introduce inconsistencies (native-only)

Supporting both allows flexibility without sacrificing consistency.

---

## Why `rules_multitool`

We use [`rules_multitool`](https://github.com/bazel-contrib/rules_multitool) to provide:

- pinned tool versions
- checksum verification
- platform-specific binaries (Linux x64, macOS arm64)
- a uniform way to expose CLI tools via Bazel

This is particularly useful for standalone tools such as:

- `actionlint`
- `shellcheck`

The alternative would be to manually maintain platform mappings, download logic, and wrappers for each tool. At scale, that quickly turns into a parallel infrastructure effort.

---

## Why This Approach

This setup reflects the actual constraints:

- large number of users
- multiple host platforms
- mixed development workflows
- need for consistent results across local and CI

A single enforced workflow would simplify the model, but would not match how the system is used in reality.

---

## Alternatives Considered

### DevContainer only

Conceptually simple, but assumes universal adoption. In practice, that assumption does not hold, leading to gaps in reproducibility.

---

### Bazel toolchains

Technically correct and very powerful, but introduce significantly more complexity than needed for standalone CLI tools.

---

## Why Use a Niche Solution

`rules_multitool` is not widely used, and that is expected.

Most teams:

- operate on a single platform (usually Linux)
- rely on CI-only validation
- accept minor inconsistencies in local setups

Under those conditions, simpler approaches are sufficient.

Our setup differs:

- cross-platform development (Linux + macOS ARM)
- large team size
- frequent local execution of tools
- low tolerance for inconsistencies

In this context, reproducibility becomes more important than minimizing tooling layers.

---

## Source of Truth

For tools downloaded directly from upstream release artifacts that participate
in the shared lockfile-based setup, the authoritative metadata lives in the
`tools/lockfiles/*.lock.json` files.

These lockfiles define:

- supported platforms
- download URLs
- checksums
- archive or package layout

Both Bazel via `rules_multitool` and the DevContainer installation scripts
consume the same lockfiles.

Feature installation scripts must not duplicate version, URL, or checksum data
for these tools.

Tools that are currently still managed directly inside a feature script, or via
the distribution package manager, remain managed elsewhere.

---

## Using From Another Repository

There are two supported Bazel usage patterns for consumers outside this
repository.

### Option 1: Reuse the exported tool targets directly

If another repository wants to use the exact targets defined here, it can depend
on this module and run the tools through external labels.

Consumer `MODULE.bazel`:

```starlark
module(name = "consumer")

bazel_dep(name = "score_devcontainer", version = "1.4.1")
```

Then run the tools through the exported targets from this repository:

- `bazel run @score_devcontainer//tools:actionlint -- --version`
- `bazel run @score_devcontainer//tools:shellcheck -- --version`
- `bazel run @score_devcontainer//tools:ruff -- --version`

If the consumer wants local target names, it can keep option 1 and add local
aliases on top:

Consumer `BUILD.bazel`:

```starlark
alias(
    name = "shellcheck",
    actual = "@score_devcontainer//tools:shellcheck",
)

alias(
    name = "actionlint",
    actual = "@score_devcontainer//tools:actionlint",
)
```

Then run:

- `bazel run //:shellcheck -- --version`
- `bazel run //:actionlint -- --version`

This is the simplest option if the consumer wants the targets defined here, but
prefers local labels in its own repository.

### Option 2: Reuse the lockfiles, but define local targets in the consumer

If another repository wants to keep its own target names, it can import the
lockfiles exported by this repository and create its own `rules_multitool` hub.

The lockfiles are exported as files from the top-level `tools` package, so the
external labels look like this:

- `@score_devcontainer//tools:lockfiles/actionlint.lock.json`
- `@score_devcontainer//tools:lockfiles/shellcheck.lock.json`

Consumer `MODULE.bazel`:

```starlark
module(name = "consumer")

bazel_dep(name = "rules_multitool", version = "1.11.1")
bazel_dep(name = "score_devcontainer", version = "1.4.1")

multitool = use_extension("@rules_multitool//multitool:extension.bzl", "multitool")

multitool.hub(lockfile = "@score_devcontainer//tools:lockfiles/shellcheck.lock.json")
multitool.hub(lockfile = "@score_devcontainer//tools:lockfiles/actionlint.lock.json")

use_repo(multitool, "multitool")
register_toolchains("@multitool//toolchains:all")
```

Consumer `BUILD.bazel`:

```starlark
alias(
    name = "shellcheck",
    actual = "@multitool//tools/shellcheck:cwd",
)

alias(
    name = "actionlint",
    actual = "@multitool//tools/actionlint:cwd",
)
```

Then run:

- `bazel run //:shellcheck -- --version`
- `bazel run //:actionlint -- --version`

This option is useful if the consumer wants to share the pinned tool metadata
but expose its own wrapper targets.

### Version alignment

The `score_devcontainer` Bazel module version corresponds to the DevContainer
image version. Repositories that use both the DevContainer and the Bazel module
must pin the same version to ensure identical tool versions in both paths.

### Notes

- The lockfile labels above are intended as the cross-repository API for Bazel
  consumers.
- The lockfile shell installer in this directory is internal support code for
  the DevContainer image build. It is not intended as a stable cross-repository
  API.

---

## Summary

We provide:

- a **DevContainer** for convenience and quick setup
- **Bazel-based tooling** for reproducible execution outside the container

This combination allows developers to choose their workflow while ensuring consistent and predictable results across the project.
