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

ARCHITECTURE=$(dpkg --print-architecture)
KERNEL=$(uname -s)

# Read tool versions + metadata into environment variables
. /devcontainer/features/s-core-local/versions.sh /devcontainer/features/s-core-local/versions.yaml

# pre-commit, it is available via $PATH in login shells, but not in non-login shells
check "validate pre-commit is working and has the correct version" bash -c "pre-commit --version | grep '4.5.1'"

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
check "validate java is working and has the correct version" bash -c "java -version 2>&1 | grep '${openjdk_21_version}'"
check "validate JAVA_HOME is set correctly" bash -c "echo ${JAVA_HOME} | xargs readlink -f | grep \"java-21-openjdk\""

# ruff
check "validate ruff is working and has the correct version" bash -c "ruff --version | grep '${ruff_version}'"

# actionlint
check "validate actionlint is working and has the correct version" bash -c "actionlint --version | grep '${actionlint_version}'"

# yamlfmt
check "validate yamlfmt is working and has the correct version" bash -c "yamlfmt --version | grep '${yamlfmt_version}'"

# uv
check "validate uv is working and has the correct version" bash -c "uv --version | grep '${uv_version}'"
check "validate uvx is working and has the correct version" bash -c "uvx --version | grep '${uv_version}'"

# additional developer tools
check "validate gdb is working and has the correct version" bash -c "gdb --version | grep '${gdb_version}'"
check "validate gh is working and has the correct version" bash -c "gh --version | grep '${gh_version}'"
check "validate valgrind is working and has the correct version" bash -c "valgrind --version | grep '${valgrind_version}'"
if [ "${ARCHITECTURE}" = "amd64" ] || { [ "${ARCHITECTURE}" = "arm64" ] && [ "${KERNEL}" = "Darwin" ]; }; then
    check "validate codeql is working and has the correct version" bash -c "codeql --version | grep '${codeql_version}'"
    check "validate CODEQL_HOME is set correctly" bash -c "echo ${CODEQL_HOME} | grep \"/usr/local/codeql\""
fi

# Qemu target-related tools
check "validate qemu-system-aarch64 is working and has the correct version" bash -c "qemu-system-aarch64 --version | grep '${qemu_system_arm_version}'"
check "validate sshpass is working and has the correct version" bash -c "sshpass -V | grep '${sshpass_version}'"
