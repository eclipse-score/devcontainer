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

# Make Bazel available through Bazelisk, pre-download the chosen release for the
# development user, and configure completion and the Java trust store.
# install.py starts this script with bazel_version as an environment variable.
# shellcheck disable=SC2154
set -euo pipefail

# Let the bazel command use Bazelisk to select and download the requested version.
ln -sf /usr/local/bin/bazelisk /usr/local/bin/bazel

# Download the chosen Bazel release into the development user's cache and save
# shell completion for later terminals.
export USE_BAZEL_VERSION=${bazel_version}
# Run as the development user so their first Bazel call can reuse this download.
su $(ls /home) -c "bazel help completion bash > /tmp/bazel-complete.bash"
mkdir -p /etc/bash_completion.d
mv /tmp/bazel-complete.bash /etc/bash_completion.d/bazel-complete.bash
sh -c "echo 'INSTALLED_BAZEL_VERSION=${bazel_version}' >> /devcontainer/features/bazel/bazel_setup.sh"

# Make Bazel trust the same certificates as the OS, including company CAs.
echo 'startup --host_jvm_args=-Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts --host_jvm_args=-Djavax.net.ssl.trustStorePassword=changeit' >> /etc/bazel.bazelrc
