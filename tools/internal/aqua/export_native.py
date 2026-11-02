#!/usr/bin/env python3
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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Export known aqua artifact layouts to the repository's portable CLI format.

This is a bounded mapping for the migrated tools. Native aqua owns versions and
hashes; upstream registry recipes own selection. Exact filename allowlists prevent
unrelated architectures, Windows assets or duplicate GNU/musl registrations.
"""

import copy


def native_lock(packages, checksums):
    result = {}
    standard_platforms = [
        ("linux", "x86_64", "amd64"),
        ("linux", "arm64", "arm64"),
        ("macos", "arm64", "arm64"),
    ]
    for package in packages:
        identifier, tag = package["name"].rsplit("@", 1)
        name = identifier.rsplit("/", 1)[1]
        repo = identifier.rsplit("/", 1)[0] if name == "buildifier" else identifier
        version = tag.removeprefix("v")
        platforms = standard_platforms
        if name in {"apm", "opencode"}:
            platforms = [
                *standard_platforms,
                ("macos", "x86_64", "amd64"),
            ]
        prefix = (
            f"http/opencode.ai/files/bin/{version}/"
            if name == "opencode"
            else f"github_release/github.com/{repo}/{tag}/"
        )
        available = {
            e["id"][len(prefix) :]: e["checksum"].lower()
            for e in checksums["checksums"]
            if e["id"].startswith(prefix)
        }
        binaries = []
        for system, cpu, goarch in platforms:
            goos = "darwin" if system == "macos" else "linux"
            triple = (
                "aarch64-apple-darwin"
                if system == "macos"
                else ("x86_64" if cpu == "x86_64" else "aarch64")
                + "-unknown-linux-musl"
            )
            if name in {"ruff", "uv"}:
                archive = f"{name}-{triple}.tar.gz"
                member = archive.removesuffix(".tar.gz") + "/" + name
                kind = "tar.gz"
            elif name == "shellcheck":
                archive = f"shellcheck-{tag}.{goos}.{'aarch64' if cpu == 'arm64' else 'x86_64'}.tar.xz"
                member = f"shellcheck-{tag}/shellcheck"
                kind = "tar.xz"
            elif name == "actionlint":
                archive = f"actionlint_{version}_{goos}_{goarch}.tar.gz"
                member = name
                kind = "tar.gz"
            elif name == "yamlfmt":
                archive = f"yamlfmt_{version}_{'Darwin' if system == 'macos' else 'Linux'}_{'x86_64' if cpu == 'x86_64' else 'arm64'}.tar.gz"
                member = name
                kind = "tar.gz"
            elif name == "starpls":
                asset_arch = (
                    {"x86_64": "amd64", "arm64": "aarch64"}[cpu]
                    if system == "linux"
                    else cpu
                )
                archive = f"starpls-{goos}-{asset_arch}"
                member = None
                kind = None
            elif name == "apm":
                asset_arch = "x86_64" if cpu == "x86_64" else "arm64"
                directory = f"apm-{goos}-{asset_arch}"
                archive = directory + ".tar.gz"
                member = f"{directory}/apm"
                kind = "tar.gz"
            elif name == "opencode":
                asset_arch = "x64" if cpu == "x86_64" else "arm64"
                extension = ".zip" if system == "macos" else ".tar.gz"
                archive = f"opencode-{goos}-{asset_arch}{extension}"
                member = "opencode"
                kind = "zip" if extension == ".zip" else "tar.gz"
            elif name in {"bazelisk", "buildifier"}:
                archive = f"{name}-{goos}-{goarch}"
                member = None
                kind = None
            else:
                raise ValueError(f"No portable archive adapter for {identifier}")
            if archive not in available:
                raise ValueError(
                    f"Missing resolved aqua checksum: {repo}/{tag}/{archive}"
                )
            entry = dict(
                kind="archive" if member else "file",
                url=f"https://github.com/{repo}/releases/download/{tag}/{archive}",
                sha256=available[archive],
                os=system,
                cpu=cpu,
            )
            if member:
                entry.update(file=member, type=kind)
            if name == "apm":
                entry["dir"] = directory
            binaries.append(entry)
        result[name] = dict(version=version, binaries=binaries)
        if name == "uv":
            result["uvx"] = copy.deepcopy(result[name])
            for entry in result["uvx"]["binaries"]:
                entry["file"] = entry["file"].removesuffix("/uv") + "/uvx"
    return result
