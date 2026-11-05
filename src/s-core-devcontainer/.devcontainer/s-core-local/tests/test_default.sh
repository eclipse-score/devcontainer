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

check_config_volume_ownership() (
    test_home=$(mktemp -d)
    trap 'sudo rm -rf "${test_home}"' EXIT

    # Reproduce Docker's root-owned volume parents, including private permissions.
    sudo mkdir -p "${test_home}/.config/opencode" "${test_home}/.config/gh" "${test_home}/.local/share/opencode"
    sudo chown root:root "${test_home}/.config" "${test_home}/.local" "${test_home}/.local/share"
    sudo chmod 700 "${test_home}/.config" "${test_home}/.local" "${test_home}/.local/share"

    HOME="${test_home}" bash /devcontainer/features/s-core-local/fix_config_volume_ownership.sh || return 1

    for directory in .config .local .local/share; do
        [ -O "${test_home}/${directory}" ] || return 1
        [ "$(stat -c %a "${test_home}/${directory}")" = 700 ] || return 1
    done
    mkdir "${test_home}/.local/state"
)

check "config volume parents belong to the user and retain private permissions" check_config_volume_ownership

ARCHITECTURE=$(dpkg --print-architecture)
KERNEL=$(uname -s)

# Read tool versions + metadata into environment variables
eval "$(/usr/local/share/score-tools/internal/devcontainer/install.py shell-metadata)"


# Verify the system-wide uv installation exposes the catalogued release to the
# non-root user running feature tests.
check "validate pre-commit is working and has the correct version" bash -c "pre-commit --version | grep '${pre_commit_version}'"

# Common tooling
check "validate shellcheck is working and has the correct version" bash -c "shellcheck --version | grep '${shellcheck_version}'"

# For an unknown reason, dot -V reports on Ubuntu Noble a version 2.43.0, while the package has a different version.
# Hence, we have to work around that.
check "validate graphviz is working" bash -c "dot -V"
check "validate graphviz has the correct version" bash -c "dpkg -s graphviz | grep 'Version: ${graphviz_version}'"

# Other build-related tools
check "validate protoc is working and has the correct version" bash -c "protoc --version | grep 'libprotoc ${protobuf_compiler_version}'"

# Common tooling
check "validate git is working and has the correct version" bash -c "git --version | grep '${git_version}'"
check "validate git-lfs is working and has the correct version" bash -c "git lfs version | grep '${git_lfs_version}'"

# Python-related tools (a selected sub-set; others may be added later)
check "validate python3 is working and has the correct version" bash -c "python3 --version | grep '${python_version}'"
check "validate pip3 is working and has the correct version" bash -c "pip3 --version | grep '${python_version}'"
check "validate black is working and has the correct version" bash -c "black --version | grep '${python_version}'"
check "validate pytest is working and has the correct version" bash -c "pytest --version | grep '${pytest_version}'"
check "validate basedpyright is working and has the correct version" bash -c "basedpyright --version | grep '${basedpyright_version}'"
# cannot grep versions as they do not match the Python version
check "validate virtualenv is working" bash -c "virtualenv --version"
check "validate flake8 is working" bash -c "flake8 --version"
check "validate pytest is working" bash -c "pytest --version"
check "validate pylint is working" bash -c "pylint --version"

# OpenJDK
check "validate java is working and has the correct version" bash -c "java -version 2>&1 | grep '${openjdk_version}'"
# Expansion belongs to the child shell that performs the check.
# shellcheck disable=SC2016
check "validate JAVA_HOME matches javac" bash -c 'test "$(readlink -f "$JAVA_HOME")" = "$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")"'

# ruff
check "validate ruff is working and has the correct version" bash -c "ruff --version | grep '${ruff_version}'"

# actionlint
check "validate actionlint is working and has the correct version" bash -c "actionlint --version | grep '${actionlint_version}'"

# yamlfmt
check "validate yamlfmt is working and has the correct version" bash -c "yamlfmt --version | grep '${yamlfmt_version}'"

# apm
check "validate apm is working and has the correct version" bash -c "apm --version | grep '${apm_version}'"

# opencode
check "validate opencode is working and has the correct version" bash -c "opencode --version | grep '${opencode_version}'"

# uv
check "validate uv is working and has the correct version" bash -c "uv --version | grep '${uv_version}'"
check "validate uvx is working and has the correct version" bash -c "uvx --version | grep '${uvx_version}'"

# pycairo build from source (requires pkg-config and libcairo2-dev)
check "validate pycairo can be built and installed from source" bash -c "pip install --break-system-packages pycairo==1.29.0"

# additional developer tools
check "validate gdb is working and has the correct version" bash -c "gdb --version | grep '${gdb_version}'"
check "validate pkg-config is working and has the correct version" bash -c "pkg-config --version | grep '${pkg_config_version}'"
check "validate gh is working and has the correct version" bash -c "gh --version | grep '${gh_version}'"
# Debian package versions may start with an epoch, e.g. 1:3.22.0.
# ${value#*:} removes that prefix; the executable reports only 3.22.0.
check "validate valgrind is working and has the correct version" bash -c "valgrind --version | grep '${valgrind_version#*:}'"
check "validate ripgrep is working and has the correct version" bash -c "rg --version | grep '${ripgrep_version}'"
if [ "${ARCHITECTURE}" = "amd64" ] || { [ "${ARCHITECTURE}" = "arm64" ] && [ "${KERNEL}" = "Darwin" ]; }; then
    check "validate codeql is working and has the correct version" bash -c "codeql --version | grep '${codeql_version}'"
    check "validate CODEQL_HOME is set correctly" bash -c "echo ${CODEQL_HOME} | grep \"/usr/local/codeql\""
fi

# lcov
check "validate lcov is working and has the correct version" bash -c "lcov --version | grep '${lcov_version}'"

# Qemu target-related tools (strip the Debian epoch here too).
check "validate qemu-system-aarch64 is working and has the correct version" bash -c "qemu-system-aarch64 --version | grep '${qemu_system_version#*:}'"
check "validate qemu-system-x86_64 is working and has the correct version" bash -c "qemu-system-x86_64 --version | grep '${qemu_system_version#*:}'"
check "validate sshpass is working and has the correct version" bash -c "sshpass -V | grep '${sshpass_version}'"
