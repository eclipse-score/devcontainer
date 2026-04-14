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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    echo "Usage:"
    echo "  $0 run"
    echo "  $0 prepare-metadata"
    echo "  $0 print-skip-message [previous_tag]"
    echo "  $0 create-and-publish <next_tag>"
}

run_release() {
    local metadata
    metadata="$(prepare_metadata)"

    local has_changes previous_tag next_tag release_notes
    has_changes="$(printf '%s\n' "${metadata}" | grep '^has_changes=' | cut -d= -f2-)"
    previous_tag="$(printf '%s\n' "${metadata}" | grep '^previous_tag=' | cut -d= -f2-)"
    next_tag="$(printf '%s\n' "${metadata}" | grep '^next_tag=' | cut -d= -f2-)"
    release_notes="$(printf '%s\n' "${metadata}" | awk '/^release_notes<<EOF/{found=1; next} found && /^EOF$/{exit} found{print}')"

    if [[ "${has_changes}" != "true" ]]; then
        print_skip_message "${previous_tag}"
        return 0
    fi

    RELEASE_NOTES="${release_notes}" create_and_publish "${next_tag}"
}

fetch_tags() {
    git fetch --force --tags origin
}

prepare_metadata() {
    fetch_tags
    "${SCRIPT_DIR}/release_metadata.sh"
}

print_skip_message() {
    local previous_tag="${1:-}"

    if [[ -n "${previous_tag}" ]]; then
        echo "No commits since ${previous_tag}; skipping release."
    else
        echo "Repository has no releasable commits yet; skipping release."
    fi
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

    if [[ "${RELEASE_DRAFT:-false}" == "true" ]]; then
        gh_args+=(--draft)
    fi

    if [[ "${RELEASE_LATEST:-true}" == "true" ]]; then
        gh_args+=(--latest)
    fi

    gh "${gh_args[@]}"
}

COMMAND="${1:-}"
case "${COMMAND}" in
    run)
        run_release
        ;;
    prepare-metadata)
        prepare_metadata
        ;;
    print-skip-message)
        shift
        print_skip_message "${1:-}"
        ;;
    create-and-publish)
        shift
        create_and_publish "${1:-}"
        ;;
    *)
        usage
        exit 1
        ;;
esac
