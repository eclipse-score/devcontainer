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

# install.py supplies catalog version variables in the process environment.
# shellcheck disable=SC2154
set -euo pipefail

# Bazelisk + Bazel
ln -sf /usr/local/bin/bazelisk /usr/local/bin/bazel

# Pre-install a fixed Bazel version, setup the bash command completion
export USE_BAZEL_VERSION=${bazel_version}
# Bazelisk caches the release for the development user selected by Dev Containers.
su $(ls /home) -c "bazel help completion bash > /tmp/bazel-complete.bash"
mkdir -p /etc/bash_completion.d
mv /tmp/bazel-complete.bash /etc/bash_completion.d/bazel-complete.bash
sh -c "echo 'INSTALLED_BAZEL_VERSION=${bazel_version}' >> /devcontainer/features/bazel/bazel_setup.sh"

# Configure Bazel to use system trust store for SSL/TLS connections
# This is required for corporate environments with custom CA certificates
echo 'startup --host_jvm_args=-Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts --host_jvm_args=-Djavax.net.ssl.trustStorePassword=changeit' >> /etc/bazel.bazelrc
