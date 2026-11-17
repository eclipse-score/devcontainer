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

# Fills the OpenCode volume that every devcontainer on this machine shares with the
# host's OpenCode configuration and plugins. Run it once per machine, and again after
# changing plugins or configuration in ~/.config/opencode.
#
# This file is shipped inside the devcontainer image, so it can be run without cloning
# this repository. It needs only Docker and bash on the host:
#
#   docker run --rm --entrypoint cat <devcontainer-image> \
#     /usr/local/share/score-tools/opencode/populate_opencode_volume.sh | bash
#
# Nothing is mounted into devcontainers. The copy happens in a throwaway container,
# so the devcontainer.json files of the repositories do not need any changes.
#
# Environment overrides:
#   OPENCODE_VOLUME          volume to populate (default: opencode-config)
#   OPENCODE_POPULATE_IMAGE  helper image that runs the copy (default: a Node image)

set -euo pipefail

volume="${OPENCODE_VOLUME:-opencode-config}"
image="${OPENCODE_POPULATE_IMAGE:-mcr.microsoft.com/devcontainers/javascript-node:5-26}"
host_config="${HOME}/.config/opencode"

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

# Runs inside the helper container. It copies the host configuration from /opt/host-opencode
# into the volume, which is mounted at $HOME/.config/opencode. Machine-specific and secret
# files are not copied, and dependencies are installed for the container's OS and architecture.
IFS= read -r -d '' copy_script <<'COPY_SCRIPT_EOF' || true
set -uo pipefail

host_dir="/opt/host-opencode"
config_dir="${HOME}/.config/opencode"
overlay_file="${config_dir}/.container-overlay.json"

if [ ! -d "${host_dir}" ] || [ -z "$(ls -A "${host_dir}" 2>/dev/null)" ]; then
  echo "Host OpenCode config: nothing mounted at ${host_dir}, skipping."
  exit 0
fi

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Host OpenCode config: node or npm not available, skipping."
  exit 0
fi

mkdir -p "${config_dir}"

# node_modules is platform-specific and service.json holds a local password.
# The global config files are merged below instead of copied.
tar -C "${host_dir}" \
  --exclude=node_modules \
  --exclude=service.json \
  --exclude=opencode.json \
  --exclude=opencode.jsonc \
  --exclude=.DS_Store \
  -cf - . | tar -C "${config_dir}" -xf - || echo "Host OpenCode config: copy incomplete."

host_config=""
for candidate in opencode.jsonc opencode.json; do
  if [ -f "${host_dir}/${candidate}" ]; then
    host_config="${host_dir}/${candidate}"
    break
  fi
done

if [ -n "${host_config}" ]; then
  # The container's own global config (for example its MCP servers) is kept as an overlay,
  # so the host config can be regenerated on each run without losing it.
  if [ ! -f "${overlay_file}" ] && [ -f "${config_dir}/opencode.json" ]; then
    cp "${config_dir}/opencode.json" "${overlay_file}"
  fi
  overlay_arg="${overlay_file}"
  [ -f "${overlay_arg}" ] || overlay_arg="/dev/null"

  # shellcheck disable=SC2016 # the Node script is intentionally single-quoted
  node -e '
    const fs = require("fs");
    const { spawnSync } = require("child_process");
    const [overlayPath, hostPath, outPath] = process.argv.slice(1);
    const parse = (file) => {
      if (!file || file === "/dev/null" || !fs.existsSync(file)) return {};
      const text = fs.readFileSync(file, "utf8")
        .replace(/("(?:[^"\\]|\\.)*")|\/\/[^\n]*|\/\*[\s\S]*?\*\/|,(?=\s*[}\]])/g, (m, str) => str ?? "");
      return JSON.parse(text);
    };
    const isObject = (v) => v && typeof v === "object" && !Array.isArray(v);
    const merge = (base, over) => {
      if (Array.isArray(base) && Array.isArray(over)) {
        const seen = new Set();
        return [...base, ...over].filter((v) => {
          const key = JSON.stringify(v);
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        });
      }
      if (isObject(base) && isObject(over)) {
        const out = { ...base };
        for (const [key, value] of Object.entries(over)) {
          out[key] = key in base ? merge(base[key], value) : value;
        }
        return out;
      }
      return over === undefined ? base : over;
    };
    const merged = merge(parse(overlayPath), parse(hostPath));
    merged.$schema ??= "https://opencode.ai/config.json";
    fs.writeFileSync(outPath, JSON.stringify(merged, null, 2) + "\n");

    const servers = (merged.mcp && merged.mcp.servers) || {};
    for (const [name, server] of Object.entries(servers)) {
      if (server.type !== "local" || !Array.isArray(server.command) || !server.command.length) continue;
      const check = spawnSync("sh", ["-c", "command -v -- \"$1\" >/dev/null 2>&1", "sh", server.command[0]]);
      if (check.status !== 0) {
        console.error(`Host OpenCode config: MCP server "${name}" needs "${server.command[0]}", which is not installed in the container.`);
      }
    }
  ' "${overlay_arg}" "${host_config}" "${config_dir}/opencode.json" \
    || echo "Host OpenCode config: could not merge ${host_config}."
fi

install_dependencies() {
  local dir="$1"
  local lock="${dir}/package-lock.json"
  [ -f "${lock}" ] || return 0

  # The architecture is part of the stamp: native modules must be reinstalled when the
  # same volume is used on a different platform.
  local sum
  sum="$(sha256sum "${lock}" | cut -d' ' -f1)-$(uname -m)"
  if [ -f "${dir}/node_modules/.lock-sha256" ] && [ "$(cat "${dir}/node_modules/.lock-sha256")" = "${sum}" ]; then
    return 0
  fi

  echo "Host OpenCode config: installing dependencies in ${dir} ..."
  if (cd "${dir}" && npm ci --omit=dev --no-audit --no-fund); then
    echo "${sum}" > "${dir}/node_modules/.lock-sha256"
  else
    echo "Host OpenCode config: npm ci failed in ${dir}."
  fi
}

install_dependencies "${config_dir}"
for plugin_dir in "${config_dir}"/plugins/*/; do
  [ -d "${plugin_dir}" ] && install_dependencies "${plugin_dir%/}"
done

# The devcontainer user (vscode) has uid 1000 in the devcontainer images. Files copied
# from the host are owned by the host user, so the volume is chowned to that uid.
chown -R 1000:1000 "${config_dir}"
COPY_SCRIPT_EOF

docker run --rm \
  --platform "${platform}" \
  -e HOME=/root \
  -v "${host_config}:/opt/host-opencode:ro" \
  -v "${volume}:/root/.config/opencode" \
  "${image}" \
  bash -c "${copy_script}"

echo "OpenCode volume '${volume}' is populated from ${host_config}."
