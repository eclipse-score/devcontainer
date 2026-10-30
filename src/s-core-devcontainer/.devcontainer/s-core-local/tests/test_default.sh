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

installer=/usr/local/share/score-tools/internal/devcontainer/install.py
. /usr/local/share/score-tools/internal/devcontainer/load_feature_versions.sh

# Selection determines availability checks. The verifier inspects installed
# package state, requested constraints, executable access and CLI releases as
# the development user rather than comparing generated inputs with each other.
check "verify selected s-core-local tools and packages" "${installer}" verify-environment s-core-local

# These are behavioral or independent compatibility checks beyond availability.
if "${installer}" selected s-core-local graphviz; then
    check "validate Graphviz can execute" dot -V
fi
if "${installer}" selected s-core-local git; then
    check "validate Git compatibility" bash -c "git --version | grep '${git_compatibility_version}'"
fi
if "${installer}" selected s-core-local git_lfs; then
    check "validate Git LFS compatibility" bash -c "git lfs version | grep '${git_lfs_compatibility_version}'"
fi
if "${installer}" selected s-core-local gh; then
    check "validate GitHub CLI compatibility" bash -c "gh --version | grep '${gh_compatibility_version}'"
fi
if "${installer}" selected s-core-local openjdk_21; then
    check "validate Java executes" java -version
    check "validate JAVA_HOME" bash -c "test -x '${JAVA_HOME}/bin/javac'"
fi
if "${installer}" selected s-core-local black; then
    check "validate Black executes" black --version
fi
if "${installer}" selected s-core-local pkg_config && "${installer}" selected s-core-local libcairo2_dev; then
    check "validate pycairo builds from source" bash -c "pip install --break-system-packages --no-binary=pycairo pycairo==${pycairo_smoke_version}"
fi
if "${installer}" selected s-core-local codeql && [ "$(dpkg --print-architecture)" = amd64 ]; then
    check "validate CodeQL version" bash -c "codeql --version | grep '${codeql_version}'"
    check "validate CODEQL_HOME" bash -c "test '${CODEQL_HOME}' = /usr/local/codeql"
    if "${installer}" selected s-core-local codeql_coding_standards; then
        for pack in misra-c misra-cpp cert-c cert-cpp; do
            check "validate CodeQL ${pack} pack" test -d "${CODEQL_HOME}/qlpacks/codeql/${pack}-coding-standards/${codeql_coding_standards_version}"
        done
    fi
fi
