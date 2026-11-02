#!/usr/bin/env bash
# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

# mise is a setup-time tool only. Its checksum-pinned binary lives outside PATH
# and only the selected tool executables are exposed to later commands.
set -euo pipefail

prefix="${1:?mise bootstrap prefix required}"
version=2026.10.24
case "$(uname -s):$(uname -m)" in
    Linux:x86_64|Linux:amd64)
        asset="linux-x64"
        sha256=be97dbac1c0b1fe08bd8c0cf01690f4273ea9aa02ad766b98d4e20c43eb9059d
        ;;
    Linux:aarch64|Linux:arm64)
        asset="linux-arm64"
        sha256=ae1151a87d70146119f68f7378001a12f09d2a38853087ed6139b7527a55f148
        ;;
    Darwin:x86_64)
        asset="macos-x64"
        sha256=399e46f059f8ffa3f5a4321513996f13100f2bc2513e5464ba666ed4c117039a
        ;;
    Darwin:arm64|Darwin:aarch64)
        asset="macos-arm64"
        sha256=ac0ee145cb145affe3ea60623a4abdb253e5ad1f938def299e633e816c0b8523
        ;;
    *)
        echo "Pinned mise bootstrap does not support $(uname -s)/$(uname -m)." >&2
        exit 2
        ;;
esac
url="https://github.com/jdx/mise/releases/download/v${version}/mise-v${version}-${asset}"
destination="${prefix}/mise"

mkdir -p -- "${prefix}"
if [[ -f "${destination}" ]]; then
    if [[ "$(uname -s)" == "Darwin" ]]; then
        printf '%s  %s\n' "${sha256}" "${destination}" | shasum -a 256 --check --status
    else
        printf '%s  %s\n' "${sha256}" "${destination}" | sha256sum --check --status
    fi
    exit 0
fi

temporary="${destination}.tmp.$$"
trap 'rm -f -- "${temporary}"' EXIT
curl --fail --location --silent --show-error --output "${temporary}" "${url}"
if [[ "$(uname -s)" == "Darwin" ]]; then
    printf '%s  %s\n' "${sha256}" "${temporary}" | shasum -a 256 --check
else
    printf '%s  %s\n' "${sha256}" "${temporary}" | sha256sum --check
fi
chmod 755 "${temporary}"
mv -- "${temporary}" "${destination}"
