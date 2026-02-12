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

# Configure clangd to remove the -fno-canonical-system-headers flag, which is
# GCC-specific. If not done, there is an annoying error message on the first
# line of every C++ file when being displayed in Visual Studio Code.
mkdir -p ~/.config/clangd
cat > ~/.config/clangd/config.yaml <<EOF
CompileFlags:
  Remove:
    - -fno-canonical-system-headers
EOF
