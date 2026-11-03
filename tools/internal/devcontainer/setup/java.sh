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

# Set JAVA_HOME environment variable system-wide, since some tools rely on it (e.g., Bazel's rules_java)
JAVA_HOME="$(dirname "$(dirname "$(realpath "$(command -v javac)")")")"
export JAVA_HOME
echo -e "JAVA_HOME=${JAVA_HOME}\nexport JAVA_HOME" > /etc/profile.d/java_home.sh
