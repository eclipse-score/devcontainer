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

current_user_group="$(id -un):$(id -gn)"

ensure_owner() {
  local target_dir="$1"

  if [ ! -d "${target_dir}" ]; then
    echo "Error: Config Volume: ${target_dir} does not exist."
    exit 1
  fi

  local current_owner_group
  current_owner_group=$(stat -c "%U:%G" "${target_dir}")

  if [ "${current_owner_group}" = "${current_user_group}" ]; then
    echo "Config Volume: ${target_dir} is already owned by ${current_user_group}."
  else
    echo "Config Volume: ${target_dir} is owned by ${current_owner_group}. Setting ownership to ${current_user_group}..."
    sudo chown -R "${current_user_group}" "${target_dir}"
  fi
}

# Docker creates missing parents of nested volume mounts as root. These are
# user-owned XDG directories; writable mount roots alone do not let tools create
# sibling state/cache directories. Change only the parents, not their contents.
sudo install -d -o "$(id -un)" -g "$(id -gn)" \
  "${HOME}/.config" "${HOME}/.local" "${HOME}/.local/share"

ensure_owner "${HOME}/.config/opencode"
ensure_owner "${HOME}/.local/share/opencode"
ensure_owner "${HOME}/.config/gh"
