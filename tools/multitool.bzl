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

"""Helpers for exposing `rules_multitool` tools as local aliases."""

def multitool_aliases(name):
    """Creates aliases for a rules_multitool tool.

    Two aliases are created:

    - `<name>` points at the `:cwd` target, which runs the tool in the
      caller's working directory (intended for `bazel run`).
    - `<name>_binary` points at the raw executable target, intended for use
      as a tool/executable dependency inside other Bazel rules.
    """

    native.alias(
        name = name,
        actual = "@multitool//tools/{0}:cwd".format(name),
    )

    native.alias(
        name = name + "_binary",
        actual = "@multitool//tools/{0}:{0}".format(name),
    )
