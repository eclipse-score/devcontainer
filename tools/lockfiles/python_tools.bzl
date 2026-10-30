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

"""Compatibility export; the Python package owns the literal definitions."""

# Preserve the exported Bazel metadata label for existing consumers without
# maintaining a second dictionary or another set of package versions.
load("//tools:score_tools/python_tools.bzl", _PYTHON_TOOLS = "PYTHON_TOOLS")

PYTHON_TOOLS = _PYTHON_TOOLS
