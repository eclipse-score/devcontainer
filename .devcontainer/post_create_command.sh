#!/usr/bin/env bash

# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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

npm install -g @devcontainers/cli
pre-commit install

scripts/create_builder.sh

sudo apt-get update && sudo apt-get install -y shellcheck

sudo mkdir -p /devcontainer/features
sudo cp --recursive src/s-core-devcontainer/.devcontainer/bazel-feature /devcontainer/features/bazel
sudo cp --recursive src/s-core-devcontainer/.devcontainer/s-core-local /devcontainer/features/

sudo src/s-core-devcontainer/.devcontainer/bazel-feature/install.sh
