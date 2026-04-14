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

usage() {
    echo "Usage:"
    echo "  $0 [GH_TOKEN]"
}

run_release() {
    prepare_metadata

    if [[ "${has_changes}" != "true" ]]; then
        echo "No commits since ${LATEST_TAG}; skipping release."
        return 0
    fi

    create_and_publish "${NEXT_TAG}"
}

fetch_tags() {
    git fetch --force --tags origin
}

prepare_metadata() {
    fetch_tags

    LATEST_TAG="$(git tag --list 'v[0-9]*.[0-9]*.[0-9]*' --sort=-version:refname | head -n 1 || true)"
    BASE_VERSION="0.0.0"
    REVISION_RANGE="HEAD"

    if [[ -n "${LATEST_TAG}" ]]; then
        BASE_VERSION="${LATEST_TAG#v}"
        REVISION_RANGE="${LATEST_TAG}..HEAD"
    fi

    COMMIT_COUNT="$(git rev-list --count "${REVISION_RANGE}")"

    if [[ "${COMMIT_COUNT}" == "0" ]]; then
        has_changes=false
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

    has_changes=true
    RELEASE_NOTES="## Release summary\n"
    RELEASE_NOTES+=$'\n'
    RELEASE_NOTES+="- Previous release: ${LATEST_TAG}\n"
    RELEASE_NOTES+="- Version bump: ${RELEASE_TYPE}\n"
    RELEASE_NOTES+="- Included commits: ${COMMIT_COUNT}\n"
    RELEASE_NOTES+=$'\n'
    RELEASE_NOTES+="## Changes\n"
    RELEASE_NOTES+=$'\n'
    RELEASE_NOTES+="${CHANGELOG}\n"
}

create_and_publish() {
    local next_tag="${1:-}"

    if [[ -z "${next_tag}" ]]; then
        echo "Error: next_tag is required."
        usage
        exit 1
    fi

    if [[ -z "${GH_TOKEN:-}" ]]; then
        echo "Error: GH_TOKEN is required to create a GitHub release."
        exit 1
    fi

    if [[ -z "${RELEASE_NOTES:-}" ]]; then
        echo "Error: RELEASE_NOTES is required."
        exit 1
    fi

    fetch_tags

    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

    if git rev-parse -q --verify "refs/tags/${next_tag}" >/dev/null; then
        echo "Error: tag ${next_tag} already exists."
        exit 1
    fi

    git tag -a "${next_tag}" -m "chore(release): ${next_tag}"
    git push origin "${next_tag}"

    local notes_file
    notes_file="$(mktemp)"
    trap 'rm -f "${notes_file}"' EXIT

    printf '%s\n' "${RELEASE_NOTES}" > "${notes_file}"

    local -a gh_args
    gh_args=(release create "${next_tag}" --title "${next_tag}" --notes-file "${notes_file}")

    # remove when everything works as expected
    gh_args+=(--draft)

    if [[ "${RELEASE_LATEST:-true}" == "true" ]]; then
        gh_args+=(--latest)
    fi

    gh "${gh_args[@]}"
}

GH_TOKEN="${1:-}"
if [[ -z "${GH_TOKEN}" ]]; then
    echo "Error: GH_TOKEN is required to run the release process."
    usage
    exit 1
fi

export GH_TOKEN
run_release
