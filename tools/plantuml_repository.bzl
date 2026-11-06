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
    for name, mode in [("plantuml", "cwd"), ("plantuml_binary", "action")]:
        ctx.template(
            name + ".sh",
            ctx.path(ctx.attr._launcher),
            {
                "@MODE@": mode,
                "@BINARY@": ctx.name + "/bundle/" + binary["file"],
            },
        )
    ctx.file("BUILD.bazel", """
load("@rules_shell//shell:sh_binary.bzl", "sh_binary")

package(default_visibility = ["//visibility:public"])

[
    sh_binary(
        name = name,
        srcs = [name + ".sh"],
        data = glob(["bundle/**"]) + ["@bazel_tools//tools/bash/runfiles"],
    )
    for name in ["plantuml", "plantuml_binary"]
]
""")

plantuml_repository = repository_rule(
    implementation = _plantuml_repository_impl,
    attrs = {
        "lockfile": attr.label(mandatory = True, allow_single_file = True),
        "_launcher": attr.label(default = Label("//tools:internal/run_plantuml.sh"), allow_single_file = True),
    },
)
