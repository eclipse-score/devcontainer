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

# Continuous Integration

The CI workflow (`.github/workflows/ci.yaml`) validates the devcontainer on every pull request, push to `main`, and merge group event.

Builds run on two architectures in parallel:

- **AMD64**
- **ARM64**

The S-CORE devcontainer is build using this repo's `.devcontainer` to ensure consistent behavior at developer and CI.

## Merge Job (main only)

Each architecture is built and tested individually.
After both architecture builds succeed, a merge job creates a multi-arch manifest and pushes it to `ghcr.io`.
It would have been ideal if the multi-arch image could have been build in one go, but that did not work.

## Consumer Tests

At consumer tests, repos using the devcontainer are build and tested using the newly created devcontainer image.
This is done to detect breaking changes before releasing a new devcontainer image and to reduce manual testing efforts.

By default these are not run in pull requests, but in the merge queue and pushes to main to save time.
If these shall be run in the pull request add the **`test-consumer`** label to a pull request.

## Release Automation

Releases are cut automatically once per week from `main`, but only if commits were added since the latest `v<major>.<minor>.<patch>` tag.
The scheduled workflow creates the git tag and GitHub release, and the existing tag-triggered release workflow then builds, tests and publishes the matching container image.

The next semantic version is derived from commit messages since the previous release:

* breaking changes (`!` in the conventional commit header or `BREAKING CHANGE:` in the body) increment the major version
* `feat` commits increment the minor version
* every other commit increments the patch version so maintenance-only weeks still publish a new immutable image
