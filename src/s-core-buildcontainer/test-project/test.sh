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

source "test-utils.sh" vscode

# Tests from the local s-core-build feature
source /devcontainer/features/s-core-build/tests/test_default.sh

# Tests from the local bazel feature
source /devcontainer/features/bazel/tests/test_default.sh

# Report result
reportResults
