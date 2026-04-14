#!/usr/bin/env bash

# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -euo pipefail

LATEST_TAG="$(git tag --list 'v[0-9]*.[0-9]*.[0-9]*' --sort=-version:refname | head -n 1 || true)"
BASE_VERSION="0.0.0"
REVISION_RANGE="HEAD"

if [[ -n "${LATEST_TAG}" ]]; then
    BASE_VERSION="${LATEST_TAG#v}"
    REVISION_RANGE="${LATEST_TAG}..HEAD"
fi

COMMIT_COUNT="$(git rev-list --count "${REVISION_RANGE}")"

if [[ "${COMMIT_COUNT}" == "0" ]]; then
    echo "has_changes=false"
    echo "previous_tag=${LATEST_TAG}"
    echo "next_version="
    echo "next_tag="
    echo "release_type="
    echo "commit_count=0"
    echo "release_notes<<EOF"
    echo "No commits since the last release."
    echo "EOF"
    exit 0
fi

# Default to a patch bump for any change. Conventional commits can then
# raise the bump to minor or major.
BUMP_LEVEL=1
RELEASE_TYPE="patch"

while IFS= read -r COMMIT_HASH; do
    SUBJECT="$(git show -s --format=%s "${COMMIT_HASH}")"
    BODY="$(git show -s --format=%b "${COMMIT_HASH}")"

    if printf '%s\n%s' "${SUBJECT}" "${BODY}" | grep -qiE '(^[a-z]+(\([^)]+\))?!:)|(^|[[:space:]])BREAKING CHANGE:'; then
        BUMP_LEVEL=3
        RELEASE_TYPE="major"
        break
    fi

    if [[ "${BUMP_LEVEL}" -lt 2 ]] && printf '%s\n' "${SUBJECT}" | grep -qE '^feat(\([^)]+\))?:'; then
        BUMP_LEVEL=2
        RELEASE_TYPE="minor"
    fi
done < <(git rev-list --reverse "${REVISION_RANGE}")

IFS='.' read -r MAJOR MINOR PATCH <<< "${BASE_VERSION}"

case "${BUMP_LEVEL}" in
    3)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    2)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    *)
        PATCH=$((PATCH + 1))
        ;;
esac

NEXT_VERSION="${MAJOR}.${MINOR}.${PATCH}"
NEXT_TAG="v${NEXT_VERSION}"
CHANGELOG="$(git log --reverse --format='* %s (%h)' "${REVISION_RANGE}")"

echo "has_changes=true"
echo "previous_tag=${LATEST_TAG}"
echo "next_version=${NEXT_VERSION}"
echo "next_tag=${NEXT_TAG}"
echo "release_type=${RELEASE_TYPE}"
echo "commit_count=${COMMIT_COUNT}"
echo "release_notes<<EOF"
echo "## Release summary"
echo
if [[ -n "${LATEST_TAG}" ]]; then
    echo "- Previous release: ${LATEST_TAG}"
else
    echo "- Previous release: none"
fi
echo "- Version bump: ${RELEASE_TYPE}"
echo "- Included commits: ${COMMIT_COUNT}"
echo
echo "## Changes"
echo
printf '%s\n' "${CHANGELOG}"
echo "EOF"
