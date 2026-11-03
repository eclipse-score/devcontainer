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

# shellcheck disable=SC2016
# Variables in strings with single quotes are expected to be evaluated later by `eval`

set -euo pipefail

# Copy feature sources and tests to expected location
FEATURES_DIR="/devcontainer/features"
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")
mkdir -p "${FEATURES_DIR}"
COPY_TARGET="${FEATURES_DIR}/$(basename "${SCRIPT_DIR%%_*}")"
cp -R "${SCRIPT_DIR}" "${COPY_TARGET}"
rm -f "${COPY_TARGET}/devcontainer-features.env" "${COPY_TARGET}/devcontainer-features-install.sh"

# shellcheck disable=SC2034
# used by apt-get only inside this script
export DEBIAN_FRONTEND=noninteractive

# Read tool versions + metadata into environment variables
. /usr/local/share/score-tools/internal/devcontainer/load_feature_versions.sh

ARCHITECTURE=$(dpkg --print-architecture)
KERNEL=$(uname -s)

apt-get update

# Unminimize the image to include standard packages like man pages
bash -c "yes || true" | unminimize

# INSTALL CONTAINER BUILD DEPENDENCIES
# Container build dependencies are not pinned, since they are removed anyway after container creation.
/usr/local/share/score-tools/internal/devcontainer/install.py install-environment s-core-local --phase build

# One environment selection owns APT, native and Python membership. Provider
# installation runs before tool-specific lifecycle configuration below.
/usr/local/share/score-tools/internal/devcontainer/install.py install-environment s-core-local

if /usr/local/share/score-tools/internal/devcontainer/install.py selected s-core-local openjdk_21; then
    # OpenJDK 21, via APT
    # Set JAVA_HOME environment variable system-wide, since some tools rely on it (e.g., Bazel's rules_java)
    JAVA_HOME="$(dirname "$(dirname "$(realpath "$(command -v javac)")")")"
    export JAVA_HOME
    echo -e "JAVA_HOME=${JAVA_HOME}\nexport JAVA_HOME" > /etc/profile.d/java_home.sh

fi

# Special setup also consumes environment membership, so removing a selection
# removes its installation rather than only changing the generated overview.
if /usr/local/share/score-tools/internal/devcontainer/install.py selected s-core-local codeql; then
    # CodeQL
    if [ "${ARCHITECTURE}" = "amd64" ]; then
        VARIANT=linux64
        SHA256SUM="${codeql_amd64_sha256}"
    elif [ "${ARCHITECTURE}" = "arm64" ]; then
        if [ "${KERNEL}" = "Darwin" ]; then
            VARIANT=osx64
            SHA256SUM="${codeql_arm64_sha256}"
        else
            echo "CodeQl unsupported architecture/os: ${ARCHITECTURE} on ${KERNEL}, skipping installation"
            VARIANT=noinstall
        fi
    else
        echo "Unsupported architecture: ${ARCHITECTURE} for CodeQL"
        exit 1
    fi

    if [ "${VARIANT}" != "noinstall" ]; then
        codeql_install_dir="/usr/local"
        curl -L "https://github.com/github/codeql-action/releases/download/codeql-bundle-v${codeql_version}/codeql-bundle-${VARIANT}.tar.zst" -o /tmp/codeql.tar.zst
        echo "${SHA256SUM} /tmp/codeql.tar.zst" | sha256sum -c - || exit 1
        tar -I zstd -xf /tmp/codeql.tar.zst -C "${codeql_install_dir}"
        ln -s "${codeql_install_dir}"/codeql/codeql /usr/local/bin/codeql
        rm /tmp/codeql.tar.zst
        export CODEQL_HOME=${codeql_install_dir}/codeql
        echo "export CODEQL_HOME=${codeql_install_dir}/codeql" > /etc/profile.d/codeql.sh

        if /usr/local/share/score-tools/internal/devcontainer/install.py selected s-core-local codeql_coding_standards; then
            codeql_packs="$(/usr/local/share/score-tools/internal/devcontainer/install.py items codeql_coding_standards packs)"
            while IFS= read -r pack; do
                codeql pack download "${pack}@${codeql_coding_standards_version}" -d "${codeql_install_dir}/codeql/qlpacks/"
            done <<< "${codeql_packs}"
        fi

        # slim down codeql bundle (1.7GB -> 1.1 GB) by removing unnecessary language extractors and qlpacks
        codeql_purge_dirs=(
            "${codeql_install_dir}/codeql/csharp"
            "${codeql_install_dir}/codeql/go"
            "${codeql_install_dir}/codeql/java"
            "${codeql_install_dir}/codeql/javascript"
            "${codeql_install_dir}/codeql/python"
            "${codeql_install_dir}/codeql/qlpacks/codeql/csharp-all"
            "${codeql_install_dir}/codeql/qlpacks/codeql/csharp-examples"
            "${codeql_install_dir}/codeql/qlpacks/codeql/csharp-queries"
            "${codeql_install_dir}/codeql/qlpacks/codeql/go-all"
            "${codeql_install_dir}/codeql/qlpacks/codeql/go-examples"
            "${codeql_install_dir}/codeql/qlpacks/codeql/go-queries"
            "${codeql_install_dir}/codeql/qlpacks/codeql/java-all"
            "${codeql_install_dir}/codeql/qlpacks/codeql/java-examples"
            "${codeql_install_dir}/codeql/qlpacks/codeql/java-queries"
            "${codeql_install_dir}/codeql/qlpacks/codeql/javascript-all"
            "${codeql_install_dir}/codeql/qlpacks/codeql/javascript-examples"
            "${codeql_install_dir}/codeql/qlpacks/codeql/javascript-queries"
            "${codeql_install_dir}/codeql/qlpacks/codeql/python-all"
            "${codeql_install_dir}/codeql/qlpacks/codeql/python-examples"
            "${codeql_install_dir}/codeql/qlpacks/codeql/python-queries"
            "${codeql_install_dir}/codeql/qlpacks/codeql/ruby-all"
            "${codeql_install_dir}/codeql/qlpacks/codeql/ruby-examples"
            "${codeql_install_dir}/codeql/qlpacks/codeql/ruby-queries"
            "${codeql_install_dir}/codeql/qlpacks/codeql/swift-all"
            "${codeql_install_dir}/codeql/qlpacks/codeql/swift-queries"
            "${codeql_install_dir}/codeql/ruby"
            "${codeql_install_dir}/codeql/swift"
        )
        for dir in "${codeql_purge_dirs[@]}"; do
            if [ -d "${dir}" ]; then
                rm -rf "${dir}"
            fi
        done
    fi

fi

# Cleanup
# REMOVE CONTAINER BUILD DEPENDENCIES
/usr/local/share/score-tools/internal/devcontainer/install.py install-environment s-core-local --phase cleanup
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
