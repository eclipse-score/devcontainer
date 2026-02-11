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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

set -euo pipefail

# Enable persistent Bazel cache
#
# Usually, a volume is mounted to /var/cache/bazel (see
# devcontainer-feature.json). This shall be used as Bazel cache, which is then
# preserved across container re-starts. Since the volume has a fixed
# name ("eclipse-s-core-bazel-cache"), it is even used across all Eclipse
# S-CORE DevContainer instances.
if [ -d /var/cache/bazel ]; then
  echo "Bazel Cache: /var/cache/bazel exists. Checking ownership and configuring Bazel to use it as cache..."
  current_owner_group=$(stat -c "%U:%G" /var/cache/bazel)
  current_user_group="$(id -un):$(id -gn)"
  if [ "${current_owner_group}" = "${current_user_group}" ]; then
    echo "Bazel Cache: /var/cache/bazel is already owned by ${current_user_group}. "
  else
    echo "Bazel Cache: /var/cache/bazel is not owned by ${current_owner_group}. Setting ownership (this may take a few seconds) ..."
    sudo chown -R "${current_user_group}" /var/cache/bazel
  fi
  echo "Bazel Cache: Configuring Bazel to use /var/cache/bazel as cache..."
  echo "startup --output_user_root=/var/cache/bazel" >> ~/.bazelrc
fi
