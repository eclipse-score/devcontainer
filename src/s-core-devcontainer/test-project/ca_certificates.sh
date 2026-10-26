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

# Sourced by test.sh, which provides the `check` helper.

# System trust store
#
# The October 2026 eMudhra incident compromised intermediate CA private keys
# chaining to "emSign ECC Root CA - G3"; Ubuntu distrusts that root as of
# ca-certificates 20260816ubuntu0.24.04.1. The Dockerfile upgrades the
# package, but image builds run with `--cache-from`, so a layer assembled
# before that upgrade could still be reused. Asserting the outcome here means
# a stale trust store fails CI instead of being published.
distrusted_root_cn="emSign ECC Root CA - G3"
distrusted_root_sha256="86:A1:EC:BA:08:9C:4A:8D:3B:BE:27:34:C6:12:BA:34:1D:81:3E:04:3C:F9:E8:A8:62:CD:5C:57:A3:6B:BE:6B"

# Prove the bundle is readable first; otherwise the absence check below would
# pass simply because nothing could be parsed out of it.
check "validate the system CA bundle is present and parsable" bash -c \
    "[ \"\$(openssl crl2pkcs7 -nocrl -certfile /etc/ssl/certs/ca-certificates.crt | openssl pkcs7 -print_certs -noout | grep -c '^subject=')\" -gt 50 ]"
check "validate the compromised ${distrusted_root_cn} is not in the system CA bundle" bash -c \
    "! openssl crl2pkcs7 -nocrl -certfile /etc/ssl/certs/ca-certificates.crt | openssl pkcs7 -print_certs -noout | grep -qF '${distrusted_root_cn}'"

# Bazel runs its JVM against this keystore (see the bazel feature's
# /etc/bazel.bazelrc), so it needs the same guarantee as the OpenSSL bundle.
# Matched on fingerprint because the keytool alias is derived from a filename.
# As above, prove the keystore is readable first, so a missing or corrupt
# keystore cannot make the absence check pass.
check "validate the Java keystore is present and parsable" bash -c \
    "[ \"\$(keytool -list -keystore /etc/ssl/certs/java/cacerts -storepass changeit | grep -c 'trustedCertEntry')\" -gt 50 ]"
check "validate the compromised ${distrusted_root_cn} is not in the Java keystore" bash -c \
    "! keytool -list -keystore /etc/ssl/certs/java/cacerts -storepass changeit | grep -qiF '${distrusted_root_sha256}'"
