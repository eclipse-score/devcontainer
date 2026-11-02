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
"""Prepare native mise selections at fixed prefixes; never run in the consumer image."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib


def environment(root):
    state = Path(
        os.environ.get("SCORE_MISE_REFERENCE_STATE", "/tmp/score-mise-evaluation-fresh")
    )
    env = dict(os.environ)
    for key, suffix in {
        "MISE_CONFIG_DIR": "config",
        "MISE_SYSTEM_CONFIG_DIR": "system-config",
        "MISE_CACHE_DIR": "cache",
        "MISE_STATE_DIR": "state",
        "UV_CACHE_DIR": "uv-cache",
        "UV_PYTHON_INSTALL_DIR": "uv-python",
    }.items():
        env[key] = str(state / suffix)
    # Installation prefixes are embedded in Python entrypoint shebangs. Keep
    # them stable in the consuming image while all mutable producer state stays
    # under the task-specific temporary directory.
    env["MISE_DATA_DIR"] = os.environ.get("SCORE_MISE_DATA_DIR", str(state / "data"))
    env.update(MISE_YES="1", MISE_TRUSTED_CONFIG_PATHS=str(root), PATH="/usr/bin:/bin")
    return env


def command(root, profile, *args, capture=False, envs=None):
    mise = os.environ.get("MISE_BINARY")
    if not mise:
        raise RuntimeError(
            "Set absolute MISE_BINARY; bootstrap.sh installs isolated mise"
        )
    profiles = envs or (
        "native,python" + (",published" if profile == "published" else "")
    )
    return subprocess.run(
        [mise, "-C", str(root), "-E", profiles, *args],
        env=environment(root),
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )


def provision(root, profile):
    if profile not in ("published", "repository"):
        raise ValueError("unknown profile")
    # Read the immutable owner selections directly. `mise ls` can refresh lock
    # metadata for the producer's host, which must not alter a release input.
    env = environment(root)
    owner_files = ["mise.native.toml", "mise.python.toml"]
    if profile == "published":
        owner_files.append("mise.published.toml")
    selections = {}
    for name in owner_files:
        with (root / name).open("rb") as handle:
            selections.update(tomllib.load(handle)["tools"])
    native = sorted(
        backend for backend in selections if not backend.startswith("pypi:")
    )
    python = sorted(backend for backend in selections if backend.startswith("pypi:"))
    if native:
        native_envs = "native,published" if profile == "published" else "native"
        command(root, profile, "install", "--locked", *native, envs=native_envs)
    if python:
        # Keep native owners out of this config load: mise may refresh native
        # lock metadata when resolving a Python tool without --locked.
        command(root, profile, "install", *python, envs="python")
    # Backend identity and extra executable names are the bounded adapter map;
    # active native env configuration owns membership and selected versions.
    names = {
        "aqua:rhysd/actionlint": ["actionlint"],
        "aqua:bazelbuild/bazelisk": ["bazelisk"],
        "aqua:bazelbuild/buildtools/buildifier": ["buildifier"],
        "aqua:astral-sh/ruff": ["ruff"],
        "pypi:pre-commit": ["pre-commit"],
        "pypi:codespell": ["codespell"],
        "aqua:koalaman/shellcheck": ["shellcheck"],
        "aqua:google/yamlfmt": ["yamlfmt"],
        "github:microsoft/apm": ["apm"],
        "aqua:anomalyco/opencode": ["opencode"],
        "github:withered-magic/starpls": ["starpls"],
        "uv": ["uv", "uvx"],
        "pypi:pytest": ["pytest"],
        "pypi:basedpyright": ["basedpyright", "basedpyright-langserver"],
    }
    paths = {}
    data_root = Path(env["MISE_DATA_DIR"])
    for backend, version in selections.items():
        if backend not in names:
            continue
        install = (
            data_root
            / "installs"
            / backend.replace(":", "-").replace("/", "-")
            / version
        )
        for name in names[backend]:
            candidates = [
                path
                for path in install.rglob(name)
                if path.is_file() and os.access(path, os.X_OK)
            ]
            # mise may expose a binary both directly and through .mise-bins;
            # collapse aliases before requiring a unique executable.
            executables = {path.resolve() for path in candidates}
            if not install.is_dir() or len(executables) != 1:
                raise RuntimeError(
                    f"Expected one installed executable {name!r} under {install}; "
                    f"found {len(executables)}"
                )
            executable = executables.pop()
            paths[name] = {
                "version": version,
                "root": str(install),
                "bin": str(executable.parent),
            }
    (root / f"{profile}.runtime.json").write_text(json.dumps(paths, indent=2) + "\n")
    return paths


if __name__ == "__main__":
    provision(Path(__file__).resolve().parent, sys.argv[1])
