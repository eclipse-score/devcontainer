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

# shellcheck shell=bash

set -euo pipefail

# Shared shell helpers around the `tools/lockfiles/*.lock.json` catalog.
#
# This script is meant to be sourced by devcontainer feature installers and
# tests. It delegates JSON parsing and platform selection to
# `tool_lockfile_query.py`, then adds the shell ergonomics needed for
# installation.
#
# Provided functions:
# - score_tool_version <tool> [lockfile]
# - score_install_tool_from_lockfile <tool> [lockfile] [destination]
#
# Example:
#   source /usr/local/share/score-tools/tool_lockfile_helpers.sh
#   score_tool_version shellcheck
#   score_install_tool_from_lockfile buildifier
#
# Direct usage:
#   bash ./tool_lockfile_helpers.sh install shellcheck yamlfmt
#   bash ./tool_lockfile_helpers.sh version shellcheck

# Resolve the helper location once when the file is sourced. This keeps the
# script self-contained: as long as the `.sh`, `.py`, and `lockfiles/`
# directory stay together, callers do not need to pass any path configuration.
SCORE_TOOL_HELPERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
readonly SCORE_TOOL_HELPERS_DIR
readonly SCORE_TOOL_LOCKFILE_QUERY_PY="${SCORE_TOOL_HELPERS_DIR}/tool_lockfile_query.py"

_score_run_tool_lockfile_query() {
    # Use the Python helper for all JSON parsing and platform selection.
    python3 "${SCORE_TOOL_LOCKFILE_QUERY_PY}" "$@"
}

score_tool_version() {
    # Print the declared version for one tool entry.
    local tool_name="$1"
    local lockfile_name="${2:-$1}"

    _score_run_tool_lockfile_query \
        version \
        --lockfile "${lockfile_name}" \
        --tool "${tool_name}"
}

score_install_tool_from_lockfile() {
    # Download, verify, extract if needed, and install one lockfile-defined
    # tool. The lockfile tells us which URL, checksum, archive type, and
    # in-archive path belong to the current platform.
    local tool_name="$1"
    local lockfile_name="${2:-$1}"
    local destination="${3:-/usr/local/bin/${tool_name}}"

    local kind=""
    local url=""
    local sha256=""
    local file=""
    local archive_type=""

    # Convert the Python helper's `key=value` output into normal shell
    # variables. We keep the mapping explicit so it is obvious which pieces of
    # metadata the installer consumes.
    while IFS='=' read -r key value; do
        case "${key}" in
            kind) kind="${value}" ;;
            url) url="${value}" ;;
            sha256) sha256="${value}" ;;
            file) file="${value}" ;;
            type) archive_type="${value}" ;;
            *) ;;
        esac
    done < <(
        _score_run_tool_lockfile_query \
            env \
            --lockfile "${lockfile_name}" \
            --tool "${tool_name}"
    )

    if [[ -z "${kind}" || -z "${url}" || -z "${sha256}" ]]; then
        echo "Incomplete lockfile metadata for ${tool_name}" >&2
        return 1
    fi

    # Work in a temporary directory so partially downloaded archives do not
    # pollute the filesystem and cleanup is automatic on return.
    local temp_dir
    temp_dir="$(mktemp -d)"
    trap 'rm -rf "${temp_dir}"; trap - RETURN' RETURN

    local download_path="${temp_dir}/download"

    # Always verify the checksum before we execute or unpack anything.
    curl -fsSL "${url}" -o "${download_path}"
    echo "${sha256} ${download_path}" | sha256sum -c - >/dev/null

    case "${kind}" in
        file)
            # Simple case: the downloaded file is the final executable.
            install -D -m 0755 "${download_path}" "${destination}"
            ;;
        archive)
            case "${archive_type}" in
                tar.gz|tgz)
                    # Extract only the requested member from the tarball.
                    tar -xzf "${download_path}" -C "${temp_dir}" "${file}"
                    install -D -m 0755 "${temp_dir}/${file}" "${destination}"
                    ;;
                tar.xz|txz)
                    # Same as above, but for xz-compressed tarballs.
                    tar -xJf "${download_path}" -C "${temp_dir}" "${file}"
                    install -D -m 0755 "${temp_dir}/${file}" "${destination}"
                    ;;
                zip)
                    # Use Python's standard-library zip support.
                    # This avoids an additional `unzip` package dependency.
                    python3 -m zipfile -e "${download_path}" "${temp_dir}" >/dev/null
                    install -D -m 0755 "${temp_dir}/${file}" "${destination}"
                    ;;
                deb|.deb)
                    # Debian packages already describe their installation
                    # layout, so we let `apt-get` handle unpacking and file
                    # placement.
                    apt-get install -y --no-install-recommends --fix-broken "${download_path}"
                    ;;
                *)
                    echo "Unsupported archive type '${archive_type}' for ${tool_name}" >&2
                    return 1
                    ;;
            esac
            ;;
        *)
            echo "Unsupported lockfile kind '${kind}' for ${tool_name}" >&2
            return 1
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    command="${1:-}"
    shift || true

    case "${command}" in
        install)
            if [[ "$#" -lt 1 ]]; then
                echo "Usage: $0 install <tool> [tool...]" >&2
                exit 2
            fi
            for tool_name in "$@"; do
                score_install_tool_from_lockfile "${tool_name}"
            done
            ;;
        version)
            if [[ "$#" -lt 1 || "$#" -gt 2 ]]; then
                echo "Usage: $0 version <tool> [lockfile]" >&2
                exit 2
            fi
            score_tool_version "$@"
            ;;
        *)
            echo "Usage: $0 <install|version> <tool> [tool...]" >&2
            exit 2
            ;;
    esac
fi
