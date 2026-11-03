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
"""Read pinned native and Python tool metadata without executing catalog code."""

# pyright: reportAny=false, reportUnusedCallResult=false, reportExplicitAny=false

from __future__ import annotations

import ast
import json
from collections.abc import Iterator
from pathlib import Path
from typing import NotRequired, TypedDict


class Binary(TypedDict):
    """A single binary entry from a tool's lockfile definition."""

    os: str
    cpu: str
    kind: str
    url: str
    sha256: str
    type: NotRequired[str]
    file: NotRequired[str]
    dir: NotRequired[str]


class ToolData(TypedDict):
    """Tool metadata from a lockfile entry."""

    version: NotRequired[str]
    description: NotRequired[str]
    binaries: list[Binary]


LOCKFILE_ROOT = Path(__file__).resolve().parents[1] / "lockfiles"
PYTHON_TOOL_CATALOG = LOCKFILE_ROOT / "python_tools.bzl"
ENVIRONMENTS_PATH = LOCKFILE_ROOT.parent / "environments.json"


class PythonTool(TypedDict):
    """Metadata shared by the container installer and Bazel launcher."""

    # The distribution and console entrypoint can have different names.
    package: str
    version: str
    entrypoint: str
    # User-facing text is kept beside the pin so generated docs cannot drift.
    description: str


def _iter_catalog() -> Iterator[tuple[str, str, ToolData]]:
    """Yield (tool, lockfile filename, definition) for every catalog entry."""
    for path in sorted(LOCKFILE_ROOT.glob("*.lock.json")):
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)

        for tool, definition in data.items():
            if tool.startswith("$"):
                continue
            if not isinstance(definition, dict):
                raise SystemExit(f"Unexpected entry '{tool}' in '{path.name}'")
            yield tool, path.name, definition


def _parse_python_tool_catalog() -> object:
    """Return the literal assigned to ``PYTHON_TOOLS``.

    The feature installer runs as root, so importing or executing a repository
    file would cross a privilege boundary. Parsing one assignment and accepting
    only literal data lets Bazel and the installer share a catalog safely.
    """
    try:
        module = ast.parse(
            PYTHON_TOOL_CATALOG.read_text(encoding="utf-8"),
            filename=str(PYTHON_TOOL_CATALOG),
        )
    except SyntaxError as exc:
        raise SystemExit(f"Malformed Python tool catalog: {exc}") from exc

    # Exactly one statement preserves the catalog's data-only contract.
    if len(module.body) != 1:
        raise SystemExit(
            "Python tool catalog must contain only a PYTHON_TOOLS assignment"
        )

    assignment = module.body[0]
    if not isinstance(assignment, ast.Assign) or len(assignment.targets) != 1:
        raise SystemExit(
            "Python tool catalog must contain only a PYTHON_TOOLS assignment"
        )

    target = assignment.targets[0]
    if not isinstance(target, ast.Name) or target.id != "PYTHON_TOOLS":
        raise SystemExit("Python tool catalog must assign its data to PYTHON_TOOLS")

    try:
        return ast.literal_eval(assignment.value)
    except (TypeError, ValueError) as exc:
        raise SystemExit("Python tool catalog must contain only literal data") from exc


def load_python_tools() -> dict[str, PythonTool]:
    """Validate the shared catalog and return typed Python tool metadata."""
    catalog = _parse_python_tool_catalog()
    if not isinstance(catalog, dict):
        raise SystemExit("PYTHON_TOOLS must be a dictionary")

    tools: dict[str, PythonTool] = {}
    for command, metadata in catalog.items():
        if (
            not isinstance(command, str)
            or not command
            or not isinstance(metadata, dict)
        ):
            raise SystemExit(f"Malformed Python tool catalog entry for '{command}'")

        package = metadata.get("package")
        version = metadata.get("version")
        entrypoint = metadata.get("entrypoint")
        description = metadata.get("description")
        # Central validation gives Bazel, installation, and documentation the
        # same required-field contract.
        if not all(
            isinstance(value, str) and value
            for value in (package, version, entrypoint, description)
        ):
            raise SystemExit(f"Malformed Python tool catalog entry for '{command}'")

        tools[command] = {
            "package": package,
            "version": version,
            "entrypoint": entrypoint,
            "description": description,
        }
    return tools


def load_catalog_versions() -> dict[str, str]:
    """Return every tool version declared by the lockfile catalog."""
    versions: dict[str, str] = {}

    for tool, filename, definition in _iter_catalog():
        version = definition.get("version")
        if not isinstance(version, str):
            raise SystemExit(
                f"Tool '{tool}' in '{filename}' does not define a string version"
            )
        if tool in versions:
            raise SystemExit(f"Tool '{tool}' is defined by multiple lockfiles")
        versions[tool] = version

    for tool, definition in load_python_tools().items():
        if tool in versions:
            raise SystemExit(f"Tool '{tool}' is defined by multiple catalogs")
        versions[tool] = definition["version"]

    return versions


def load_catalog_descriptions() -> dict[str, str]:
    """Return every tool description declared by the lockfile catalog.

    Tools without a description are omitted so callers can report a
    friendly list of undocumented tools instead of failing on the first
    one encountered.
    """
    descriptions: dict[str, str] = {}

    for tool, filename, definition in _iter_catalog():
        description = definition.get("description")
        if description is None:
            continue
        if not isinstance(description, str):
            raise SystemExit(
                f"Tool '{tool}' in '{filename}' has a non-string description"
            )
        if tool in descriptions:
            raise SystemExit(f"Tool '{tool}' is defined by multiple lockfiles")
        descriptions[tool] = description

    for tool, definition in load_python_tools().items():
        if tool in descriptions:
            raise SystemExit(f"Tool '{tool}' is defined by multiple catalogs")
        descriptions[tool] = definition["description"]

    return descriptions


def _lockfile_path(lockfile: str) -> Path:
    """Resolve a lockfile basename like `ruff` to `ruff.lock.json`."""
    return LOCKFILE_ROOT / f"{lockfile}.lock.json"


def load_tool(lockfile: str, tool: str) -> ToolData:
    """Load one tool entry from a lockfile and fail with a clear message."""
    with _lockfile_path(lockfile).open(encoding="utf-8") as handle:
        data = json.load(handle)

    try:
        return data[tool]
    except KeyError as exc:
        raise SystemExit(
            f"Tool '{tool}' not found in lockfile '{lockfile}.lock.json'",
        ) from exc


def _find_lockfile(tool: str) -> str:
    """Find the lockfile basename that declares a tool."""
    for path in sorted(LOCKFILE_ROOT.glob("*.lock.json")):
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        if tool in data:
            return path.name.removesuffix(".lock.json")

    raise SystemExit(f"Tool '{tool}' not found in lockfile catalog")


def resolve_lockfile(tool: str, lockfile: str | None = None) -> str:
    """Return the lockfile basename for *tool*, auto-detecting when needed."""
    if lockfile is not None:
        return lockfile
    if _lockfile_path(tool).exists():
        return tool
    return _find_lockfile(tool)


PROVIDERS_PATH = LOCKFILE_ROOT.parent / "providers.json"


def load_providers() -> dict:
    """Read APT, npm and feature-specific setup definitions."""
    providers = json.loads(PROVIDERS_PATH.read_text(encoding="utf-8"))
    if not isinstance(providers, dict):
        raise SystemExit("Tool providers must be a dictionary")
    for name, definition in providers.items():
        if not isinstance(definition, dict) or definition.get("provider") not in (
            "apt",
            "npm",
            "release",
            "bazelisk",
        ):
            raise SystemExit(f"Invalid provider definition for '{name}'")
        if definition["provider"] == "apt":
            if definition.get("policy") not in (
                "distribution",
                "prefix",
                "package-name",
            ):
                raise SystemExit(f"Invalid APT policy for '{name}'")
            packages = definition.get("packages")
            if (
                not isinstance(packages, list)
                or not packages
                or any(
                    not isinstance(package, str)
                    or not package
                    or package.startswith("-")
                    for package in packages
                )
            ):
                raise SystemExit(f"Invalid APT packages for '{name}'")
            if definition["policy"] != "distribution" and not definition.get("version"):
                raise SystemExit(f"Missing APT version constraint for '{name}'")
        elif definition["provider"] == "npm":
            if (
                not isinstance(definition.get("package"), str)
                or not definition["package"]
            ):
                raise SystemExit(f"Missing npm package for '{name}'")
    return providers


def all_definitions() -> dict:
    """Combine metadata for reference validation without loading repository configs."""
    tools = {}
    sources = (
        ((name, {**data, "provider": "native"}) for name, _, data in _iter_catalog()),
        (
            (name, {**data, "provider": "python", "requires": ["uv"]})
            for name, data in load_python_tools().items()
        ),
        load_providers().items(),
    )
    for source in sources:
        for name, definition in source:
            if name in tools:
                raise SystemExit(f"Duplicate tool definition: '{name}'")
            tools[name] = definition
    return tools


def load_environments() -> dict[str, dict[str, list[str]]]:
    """Validate membership, provider categories and deliberately selected dependencies."""
    data = json.loads(ENVIRONMENTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("Tool environments must be a dictionary")
    tools = all_definitions()
    categories = {
        "native": {"native"},
        "python": {"python"},
        "apt": {"apt"},
        "build-apt": {"apt"},
        "npm": {"npm"},
        "setup": {"release", "bazelisk"},
    }
    for name, selection in data.items():
        if not isinstance(name, str) or not name:
            raise SystemExit("Tool environment names must be nonempty strings")
        if not isinstance(selection, dict) or selection.keys() - categories.keys():
            raise SystemExit(f"Invalid provider categories in environment '{name}'")
        for category, names in selection.items():
            if not isinstance(names, list) or any(
                not isinstance(tool, str) or not tool for tool in names
            ):
                raise SystemExit(f"Environment '{name}/{category}' must be a tool list")
            if len(names) != len(set(names)):
                raise SystemExit(
                    f"Environment '{name}/{category}' lists a tool more than once"
                )
            for tool in names:
                if tool not in tools:
                    raise SystemExit(f"Unknown tool '{tool}' in environment '{name}'")
                if tools[tool]["provider"] not in categories[category]:
                    raise SystemExit(
                        f"Wrong provider for '{tool}' in environment '{name}/{category}'"
                    )
                if (category == "build-apt") != (
                    tools[tool].get("phase") == "build-only"
                ):
                    raise SystemExit(
                        f"Wrong installation phase for '{tool}' in environment '{name}'"
                    )
        selected = {tool for names in selection.values() for tool in names}
        for tool in selected:
            for dependency in tools[tool].get("requires", []):
                if dependency not in selected:
                    raise SystemExit(
                        f"Tool '{tool}' requires '{dependency}' in environment '{name}'"
                    )
    return data


def apt_requirements(
    selection: dict, definitions: dict, *, recommends: bool
) -> list[str]:
    """Translate selected APT policies to requests, preserving Debian epochs."""
    requirements = []
    for name in selection.get("apt", []):
        tool = definitions[name]
        if tool.get("install_recommends", True) != recommends:
            continue
        for package in tool["packages"]:
            if tool["policy"] == "package-name":
                package = package.format(version=tool["version"])
            elif tool["policy"] == "prefix":
                package += "=" + tool["version"] + "*"
            requirements.append(package)
    return requirements
