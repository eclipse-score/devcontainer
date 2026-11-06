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

"""Expose the native PlantUML executable together with its rendering libraries."""

def _plantuml_repository_impl(ctx):
    os_name = "macos" if ctx.os.name.startswith("mac") else ctx.os.name
    cpu = {"amd64": "x86_64", "aarch64": "arm64"}.get(ctx.os.arch, ctx.os.arch)
    metadata = json.decode(ctx.read(ctx.attr.lockfile))["plantuml"]
    binaries = [binary for binary in metadata["binaries"] if binary["os"] == os_name and binary["cpu"] == cpu]
    if not binaries:
        fail("No native PlantUML binary for {}/{}".format(os_name, cpu))
    binary = binaries[0]
    ctx.download_and_extract(
        url = binary["url"],
        sha256 = binary["sha256"],
        type = binary["type"],
        output = "bundle",
    )

    # The canonical repository name is known here, so the launcher can locate
    # the bundle in runfiles even when this module is used by another repository.
    ctx.template(
        "plantuml_binary.sh",
        ctx.path(ctx.attr._launcher),
        {"@BINARY@": ctx.name + "/bundle/" + binary["file"]},
    )
    ctx.symlink(ctx.path(ctx.attr._build_file), "BUILD.bazel")

plantuml_repository = repository_rule(
    implementation = _plantuml_repository_impl,
    attrs = {
        "lockfile": attr.label(mandatory = True, allow_single_file = True),
        "_build_file": attr.label(default = Label("//tools:internal/plantuml.BUILD.bazel"), allow_single_file = True),
        "_launcher": attr.label(default = Label("//tools:internal/run_plantuml.sh"), allow_single_file = True),
    },
)
