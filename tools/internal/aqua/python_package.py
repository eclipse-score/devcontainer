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
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Build standard Python dependency metadata directly from maintained owners."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tomllib

import yaml


OWNER_FILES = (
    "aqua.yaml",
    "aqua-policy.yaml",
    "aqua-bootstrap.toml",
    "aqua-checksums.json",
    "apm-registry.yaml",
    "starpls-registry.yaml",
    "pyproject.toml",
)
HEADER = (
    "# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation\n"
    "# SPDX-License-Identifier: Apache-2.0\n"
)
PACKAGE_NAME_PATTERN = re.compile(r"[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*\Z")


def dependency_groups(owner_dir: Path) -> dict[str, list]:
    """Read the Python dependency groups that own all Python tool versions."""
    data = tomllib.loads((owner_dir / "pyproject.toml").read_text(encoding="utf-8"))
    groups = data.get("dependency-groups")
    if not isinstance(groups, dict):
        raise ValueError(f"Missing dependency-groups in {owner_dir / 'pyproject.toml'}")
    return groups


def requirements(groups: dict[str, list], group: str) -> list[str]:
    """Flatten pinned dependency groups while rejecting unowned version forms."""
    result: list[str] = []
    active: set[str] = set()

    def visit(name: str) -> None:
        if name in active:
            raise ValueError(f"Recursive Python dependency group: {name}")
        try:
            entries = groups[name]
        except KeyError as exc:
            raise ValueError(f"Unknown Python dependency group: {name}") from exc
        active.add(name)
        for entry in entries:
            if isinstance(entry, dict) and set(entry) == {"include-group"}:
                visit(entry["include-group"])
            elif isinstance(entry, str) and re.fullmatch(
                r"[A-Za-z0-9_.-]+==[^\s;]+", entry
            ):
                result.append(entry)
            else:
                raise ValueError(
                    f"Unsupported pinned dependency in group {name}: {entry!r}"
                )
        active.remove(name)

    visit(group)
    return result


def selected_versions(owner_dir: Path) -> dict[str, dict[str, str]]:
    """Return each profile's tool versions using native and Python owners."""
    native = yaml.safe_load((owner_dir / "aqua.yaml").read_text(encoding="utf-8"))[
        "packages"
    ]
    groups = dependency_groups(owner_dir)
    selected: dict[str, dict[str, str]] = {}
    for profile in groups:
        versions: dict[str, str] = {}
        for package in native:
            if profile not in package["tags"]:
                continue
            name, version = package["name"].rsplit("@", 1)
            name = name.rsplit("/", 1)[-1]
            versions[name] = version.removeprefix("v")
            if name == "uv":
                versions["uvx"] = versions[name]
        for requirement in requirements(groups, profile):
            name, version = requirement.split("==", 1)
            versions[name] = version
        selected[profile] = dict(sorted(versions.items()))
    return selected


def owner_digest(owner_dir: Path) -> str:
    """Fingerprint all owner inputs which determine a local dependency release."""
    digest = hashlib.sha256()
    for name in OWNER_FILES:
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update((owner_dir / name).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def package_metadata(owner_dir: Path, version: str, package_name: str) -> str:
    """Render an installable, ordinary dependency package for the current owners."""
    if not PACKAGE_NAME_PATTERN.fullmatch(package_name):
        raise ValueError(f"Invalid Python distribution name: {package_name!r}")
    if not version:
        raise ValueError("A release version is required")

    native = yaml.safe_load((owner_dir / "aqua.yaml").read_text(encoding="utf-8"))[
        "packages"
    ]
    groups = dependency_groups(owner_dir)
    extras: dict[str, list[str]] = {}
    for profile in groups:
        profile_requirements = requirements(groups, profile)
        ruff = next(
            (
                package["name"].rsplit("@", 1)[1].removeprefix("v")
                for package in native
                if package["name"].rsplit("@", 1)[0].endswith("/ruff")
                and profile in package["tags"]
            ),
            None,
        )
        if ruff is not None:
            profile_requirements.append(f"ruff=={ruff}")
        extras[profile] = profile_requirements
        for requirement in profile_requirements:
            name = requirement.split("==", 1)[0]
            extras[name] = [requirement]

    lines = [
        HEADER.rstrip("\n"),
        "",
        "# Generated standard metadata; consumers do not execute the producer.",
        "[build-system]",
        'requires = ["setuptools>=77"]',
        'build-backend = "setuptools.build_meta"',
        "[project]",
        f"name = {json.dumps(package_name)}",
        f"version = {json.dumps(version)}",
        'requires-python = ">=3.10"',
        "[project.optional-dependencies]",
    ]
    lines.extend(
        f"{json.dumps(name)} = {json.dumps(values)}" for name, values in extras.items()
    )
    lines.extend(["[tool.setuptools]", "packages = []", ""])
    return "\n".join(lines)


def release_manifest(
    owner_dir: Path, version: str, package_name: str, wheel_name: str, wheel_sha256: str
) -> dict:
    """Bind package identity and wheel bytes to the exact selected tool owners."""
    return {
        "schema_version": 1,
        "version": version,
        "package": package_name,
        "owner_digest": owner_digest(owner_dir),
        "selection": selected_versions(owner_dir),
        "wheel": {"filename": wheel_name, "sha256": wheel_sha256},
    }
