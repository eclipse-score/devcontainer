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
"""Regenerate existing root consumer metadata from maintained tool owners.

Description/public-label fields remain existing repository metadata. Versions,
artifact registrations and Python requirements are derived from maintained
owners. This deliberately changes only migrated tools; other baseline
lockfiles remain untouched.
"""

import argparse
import ast
import json
from pathlib import Path

import yaml

from export_native import native_lock
from python_package import dependency_groups, requirements

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OWNER_DIR = REPO / "tools/owners/aqua"


def outputs(source):
    native = yaml.safe_load((source / "aqua.yaml").read_text())["packages"]
    checksums = json.loads((source / "aqua-checksums.json").read_text())
    locks = native_lock(native, checksums)
    groups = dependency_groups(source)
    files = {}
    environments = json.loads((REPO / "tools/environments.json").read_text())
    selected = []
    for package in native:
        if "repository" in package["tags"]:
            name = package["name"].rsplit("@", 1)[0].rsplit("/", 1)[1]
            selected.extend([name, "uvx"] if name == "uv" else [name])
    environments["repository"]["native"] = selected
    environments["repository"]["python"] = [
        r.split("==")[0] for r in requirements(groups, "repository")
    ]
    files[REPO / "tools/environments.json"] = json.dumps(environments, indent=2) + "\n"
    for name in locks:
        if name == "uvx":
            continue
        path = REPO / "tools/lockfiles" / f"{name}.lock.json"
        current = json.loads(path.read_text())
        current.pop("$comment", None)
        for command in [name, "uvx"] if name == "uv" else [name]:
            current[command].update(locks[command])
        files[path] = json.dumps(current, indent=2) + "\n"
    path = REPO / "tools/score_tools/python_tools.bzl"
    module = ast.parse(path.read_text())
    assignment = next(n for n in module.body if isinstance(n, ast.Assign))
    catalog = ast.literal_eval(assignment.value)
    for profile in groups:
        reqs = requirements(groups, profile)
        if any(
            p["name"].startswith("astral-sh/ruff@") and profile in p["tags"]
            for p in native
        ):
            reqs += ["ruff==" + locks["ruff"]["version"]]
        for req in reqs:
            name, selected = req.split("==", 1)
            if name == "ruff":
                continue
            catalog[name]["version"] = selected
    header = (REPO / "tools/lockfiles/python_tools.bzl").read_text().split('"""', 1)[0]
    lines = [
        header + "# Generated versions from tools/owners/aqua/pyproject.toml.",
        "# Descriptions/public command identities retain the existing catalog contract.",
        "PYTHON_TOOLS = {",
    ]
    for name, tool in catalog.items():
        lines.append("    " + json.dumps(name) + ": {")
        lines.extend(
            "        " + json.dumps(k) + ": " + json.dumps(v) + ","
            for k, v in tool.items()
        )
        lines.append("    },")
    lines.append("}")
    files[path] = "\n".join(lines) + "\n"
    return files


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--source", type=Path, default=OWNER_DIR)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for path, expected in outputs(args.source).items():
        if not path.exists() or path.read_text() != expected:
            stale.append(str(path.relative_to(REPO)))
            if not args.check:
                path.write_text(expected)
    print(
        json.dumps(
            {"mode": "check" if args.check else "write", "changed": stale}, indent=2
        )
    )
    if args.check and stale:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
