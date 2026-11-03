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

# Shared definitions are literal data. The bridge quotes values and validates
# variable names before emitting exports for provider-specific shell setup.
score_feature_metadata="$(/usr/local/share/score-tools/internal/devcontainer/install.py shell-metadata)"
eval "${score_feature_metadata}"
unset score_feature_metadata
