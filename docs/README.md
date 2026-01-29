# S-CORE DevContainer Architecture

This document explains how the S-CORE DevContainer is designed, built and what its requirements are.

## Overview

One has to take ones own medicin and for that reason the [S-CORE devcontainer](../src/) is developed using another [simpler devcontainer](../.devcontainer).

```
            Host
             │
             ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Outer Dev Container (.devcontainer)                                   │
│  Base: devcontainers/javascript-node                                  │
│  Tools: devcontainer CLI, Docker CLI                                  │
│                                                                       │
│   devcontainer build (scripts/build.sh)                               │
│            │                                                          │
│            │ invokes docker build                                     │
│            ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Build S-CORE DevContainer (src/s-core-devcontainer)             │  │
│  │  - Dockerfile (Ubuntu base image)                               │  │
│  │  - Pre-existing features (Git, LLVM/Clang, Rust, …)             │  │
│  │  - S-CORE local feature (available at /devcontainer/features/…) │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│            │                                                          │
│            ▼ run validation (scripts/test.sh)                         │
│            │                                                          │
│            │ on success                                               |
│            ▼                                                          |
│   Publish image → ghcr.io/eclipse-score/devcontainer:<tag>            |
└───────────────────────────────────────────────────────────────────────┘
```

This [simpler devcontainer](../.devcontainer) must be able to run [the devcontainer command](https://github.com/devcontainers/cli), which is a nodejs application and Docker.
To achieve that, [javascript-node](https://github.com/devcontainers/images/tree/main/src/javascript-node) as base image and the [Docker-in-Docker](https://github.com/devcontainers/features/tree/main/src/docker-in-docker) feature were chosen.

## The S-CORE DevContainer

[DR-001-Infra: Integration Strategy for External Development Tools](https://github.com/eclipse-score/score/blob/main/docs/design_decisions/DR-001-infra.md)
and
[DR-003-Infra: Devcontainer Strategy for S-CORE](https://github.com/eclipse-score/score/blob/main/docs/design_decisions/DR-003-infra.md)
require that all tools / code inside the devcontainer are pinned and that it will be used by developers and CI.
Developers and CI should only need to download prebuild container images.
The container images should be able to build all of S-CORE without extra setup.
This requires that the needed tools are preinstalled, but not too much either to keep container image download times in check.

To achieve this, a small base image [based on Ubuntu is chosen](https://github.com/docker-library/buildpack-deps/blob/master/ubuntu/noble/curl/Dockerfile).
To this image, the tools needed to build S-CORE and run its tests are added - either via pre-existing devcontainer features, or our own [S-CORE feature](../src/s-core-devcontainer/.devcontainer/s-core-local/).
The tools also need to support typical IDE features like enabling code completion.
All of these tools could have been added via a `Dockerfile` as well, but features are the mechanism to achieve composable devcontainer implementations and are preferred instead.

The decision whether to use a pre-existing feature or to add a tool using the S-CORE feature is based on the tradeoff between build time and maintainability.
The chosen features are installed quickly, without us having to maintain them.
Other tools installed via the S-CORE feature either have no corresponding feature, or their feature took so much time to install, that it was quicker done using our own code (example: Python feature).

### Proxy environments

To support proxy environments, environment variables are set in the [`Dockerfile`](../src/s-core-devcontainer/.devcontainer/Dockerfile) and unset if empty to not interfere with non-proxy environments.

## Tests

After an image build, tests check that each tool expected to be in the image is installed with the specified version for [pre-existing features](../src/s-core-devcontainer/test-project/test.sh) and the [S-CORE feature](../src/s-core-devcontainer/.devcontainer/s-core-local/tests/test_default.sh).
This may seem overly complex at first, but prevents (1) accidentially wrong versions, (2) completely broken tools that cannot even execute.
Both cases can happen and have happened in the past already, e.g. due to unexpected interactions between devcontainer features.

However it is not tested, if S-CORE can be build with that image.
The expectation is that **pinned-in-source-code** devcontainer versions are used by S-CORE repositories.
Updates of devcontainer versions thus are explicit pull-requests (which can be auto-generated via Dependabot or Renovate).
If such an image update fails to build/test/... a certain module, the version bump pull-request will fail in the CI and investigation can start.
Note that this **does not impact** the regular development of that module.

## Why this setup

This setup is predictable and fast because a pre-built image avoids per-repo Docker builds and ensures everyone shares the same toolchain.
It strengthens the supply chain by pinning versions and hashes, sourcing features from trusted catalogs, and gating publication via CI builds and tests.
Pre-built images have a higer availability than the set of all tools which are installed (one download from a location controlled by S-CORE vs. many downloads from "everywhere").
Pre-built images can be easily archived anywhere, e.g. for reproducibility of builds in real production use-cases.
It also enforces a clear separation of concerns: general tooling is delivered through reusable features, S-CORE–specific logic lives in a dedicated feature, and image composition plus publishing are centralized.
