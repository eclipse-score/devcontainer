#!/usr/bin/env bash
# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

# Assemble an immutable local release fixture. Production images use the
# direct setup-time adapter under tools/internal/mise instead.
set -euo pipefail
release="$(cd -- "$(dirname -- "$0")" && pwd -P)"
root="${1:?destination image root required}"
profile="${2:?published or repository required}"
case "${profile}" in published|repository) ;; *) exit 2 ;; esac
# Generated release paths retain complete venvs and native runtime trees.
# shellcheck source=/dev/null
source "${release}/profiles/${profile}.sh"
for prefix in "${prefixes[@]}"; do
    mkdir -p "${root}${prefix}"
    cp -a "${release}/native${prefix}/." "${root}${prefix}/"
done
mkdir -p "${root}/usr/local/bin"
for index in "${!commands[@]}"; do
    ln -sf "${executables[index]}" "${root}/usr/local/bin/${commands[index]}"
done
