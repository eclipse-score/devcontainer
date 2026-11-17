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

# Fills the OpenCode volume that every devcontainer on this machine shares with
# the host's OpenCode configuration and plugins. Run it once per machine, and again
# after changing plugins or configuration in ~/.config/opencode.
#
# Nothing is mounted into devcontainers. The copy happens in a throwaway container,
# so the devcontainer.json files of the repositories do not need any changes.
#
# Environment overrides:
#   OPENCODE_VOLUME          volume to populate (default: opencode-config)
#   OPENCODE_POPULATE_IMAGE  image used to run the copy (default: the devcontainer base image)

set -euo pipefail

SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname -- "${SCRIPT_PATH}")

volume="${OPENCODE_VOLUME:-opencode-config}"
image="${OPENCODE_POPULATE_IMAGE:-mcr.microsoft.com/devcontainers/javascript-node:5-26}"
host_config="${HOME}/.config/opencode"
sync_script="${SCRIPT_DIR}/sync_host_opencode.sh"

if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
  echo "Error: Docker is not running or not installed."
  exit 1
fi

if [ ! -d "${host_config}" ]; then
  echo "Error: ${host_config} does not exist. Set up OpenCode on this machine first."
  exit 1
fi

# The copy must match the devcontainer's platform, because the plugin's native modules
# are platform-specific. Use the daemon's native platform, not DOCKER_DEFAULT_PLATFORM.
platform="$(docker version --format '{{.Server.Os}}/{{.Server.Arch}}')"

# The devcontainer user (vscode) has uid 1000 in the devcontainer images. Files copied
# from the host are owned by the host user, so the copy is chowned to that uid.
docker run --rm \
  --platform "${platform}" \
  -e HOME=/root \
  -v "${host_config}:/opt/host-opencode:ro" \
  -v "${sync_script}:/opt/sync_host_opencode.sh:ro" \
  -v "${volume}:/root/.config/opencode" \
  "${image}" \
  bash -c 'bash /opt/sync_host_opencode.sh && chown -R 1000:1000 /root/.config/opencode'

echo "OpenCode volume '${volume}' is populated from ${host_config}."
