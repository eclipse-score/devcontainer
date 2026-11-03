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

# install.py passes version and checksum variables from providers.json.
# shellcheck disable=SC2154
set -euo pipefail

ARCHITECTURE=$(dpkg --print-architecture)
if [ "${ARCHITECTURE}" != "amd64" ]; then
    echo "No CodeQL bundle selected for Linux ${ARCHITECTURE}" >&2
    exit 1
fi
VARIANT=linux64
SHA256SUM="${codeql_amd64_sha256}"

codeql_install_dir="/usr/local"
curl -L "https://github.com/github/codeql-action/releases/download/codeql-bundle-v${codeql_version}/codeql-bundle-${VARIANT}.tar.zst" -o /tmp/codeql.tar.zst
echo "${SHA256SUM} /tmp/codeql.tar.zst" | sha256sum -c - || exit 1
tar -I zstd -xf /tmp/codeql.tar.zst -C "${codeql_install_dir}"
ln -s "${codeql_install_dir}"/codeql/codeql /usr/local/bin/codeql
rm /tmp/codeql.tar.zst
export CODEQL_HOME=${codeql_install_dir}/codeql
echo "export CODEQL_HOME=${codeql_install_dir}/codeql" > /etc/profile.d/codeql.sh

if "${SCORE_TOOLS_INSTALLER}" selected "${SCORE_TOOL_ENVIRONMENT}" codeql_coding_standards; then
    codeql_packs="$("${SCORE_TOOLS_INSTALLER}" items codeql_coding_standards packs)"
    while IFS= read -r pack; do
        codeql pack download "${pack}@${codeql_coding_standards_version}" -d "${codeql_install_dir}/codeql/qlpacks/"
    done <<< "${codeql_packs}"
fi

# Remove unused language tools and query packs to keep the image smaller.
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
