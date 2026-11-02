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
"""Read shared tool definitions without installation side effects."""

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
PYTHON_TOOL_CATALOG = Path(__file__).with_name("python_tools.bzl")


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


def _load_python_tools() -> dict[str, PythonTool]:
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

    for tool, definition in _load_python_tools().items():
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

    for tool, definition in _load_python_tools().items():
        if tool in descriptions:
            raise SystemExit(f"Tool '{tool}' is defined by multiple catalogs")
        descriptions[tool] = definition["description"]

    return descriptions


def load_providers():
    """Return provider-specific definitions owned outside native/Python catalogs."""
    return json.loads((LOCKFILE_ROOT.parent / "providers.json").read_text())


def load_environments():
    """Return environment selections; selections carry no version decisions."""
    return json.loads((LOCKFILE_ROOT.parent / "environments.json").read_text())


def apt_requirements(environment, *, recommends=None):
    """Translate selected distribution policies into apt's request syntax."""
    providers = load_providers()
    requirements = []
    for name in load_environments()[environment].get("apt", []):
        tool = providers[name]
        if (
            recommends is not None
            and tool.get("install_recommends", True) != recommends
        ):
            continue
        for package in tool["packages"]:
            if tool["policy"] == "package-name":
                package = package.format(version=tool["version"])
            elif tool["policy"] == "prefix":
                package += "=" + tool["version"] + "*"
            requirements.append(package)
    return requirements


def all_definitions(*, repository_metadata=True):
    """Unify inventory views while retaining provider-owned formats."""
    root = LOCKFILE_ROOT.parents[1]
    update_policy = "manual release + artifact digest review"
    if repository_metadata:
        managers = read_jsonc(root / ".github/renovate.json5").get(
            "enabledManagers", []
        )
        if "mise" in managers:
            update_policy = "Renovate mise manager + lock/export refresh"
    result = {}
    for name, filename, definition in _iter_catalog():
        if name in result:
            raise ValueError(f"Duplicate tool definition: {name}")
        result[name] = {
            **definition,
            "provider": "native",
            "policy": "sha256",
            "source": "tools/lockfiles/" + filename,
            "platforms": sorted(
                {b["os"] + "/" + b["cpu"] for b in definition["binaries"]}
            ),
            "delivery": "container, Bazel",
            "update": update_policy,
        }
    for name, definition in _load_python_tools().items():
        if name in result:
            raise ValueError(f"Duplicate tool definition: {name}")
        result[name] = {
            **definition,
            "provider": "python",
            "policy": "top-level exact",
            "source": "tools/score_tools/python_tools.bzl",
            "platforms": ["uv-supported platforms"],
            "delivery": "container, Bazel, uv",
            "update": update_policy,
        }
    for name, definition in load_providers().items():
        if name in result:
            raise ValueError(f"Duplicate tool definition: {name}")
        result[name] = {
            **(
                resolved_provider(name, definition)
                if repository_metadata
                else definition
            ),
            "source": definition.get("config", "tools/providers.json"),
            "delivery": "container",
        }
    return result


def validate_environment(environment, tools, *, platform=None):
    """Validate a composition before any installation side effects.

    Container images only carry tools/, so this check uses the portable catalog
    without resolving repository configs, update managers or Bazel registrations.
    """
    selections = load_environments()[environment]
    for provider, names in selections.items():
        if provider not in ("native", "python", "apt", "setup", "build-apt", "npm"):
            raise ValueError(f"Unknown composition provider: {provider}")
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate selection in {environment}/{provider}")
        for name in names:
            if name not in tools:
                raise ValueError(f"Undefined tool {name} in {environment}")
            if provider != "setup" and tools[name]["provider"] != (
                "apt" if provider == "build-apt" else provider
            ):
                raise ValueError(f"Wrong provider for {name} in {environment}")
    selected = {name for names in selections.values() for name in names}
    for name in selected:
        for dependency in tools[name].get("requires", []):
            if dependency not in selected:
                raise ValueError(f"{name} requires {dependency} in {environment}")
    if platform is not None:
        for name in selected:
            tool = tools[name]
            if (
                tool["provider"] in ("native", "apt", "release", "bazelisk")
                and platform not in tool["platforms"]
                and platform not in tool.get("omissions", {})
            ):
                raise ValueError(
                    f"{name} is unsupported on {platform} in {environment}"
                )
    for name in selections.get("apt", []):
        tool = tools[name]
        if tool["policy"] not in ("distribution", "prefix", "package-name"):
            raise ValueError(f"Unknown APT policy for {name}: {tool['policy']}")
        if tool["policy"] != "distribution" and not tool.get("version"):
            raise ValueError(f"Missing APT version constraint: {name}")
    return selections


def validate_catalog():
    """Reject undefined selections and drift in unavoidable Bazel registrations."""
    import re

    tools = all_definitions()
    # Related commands in a multitool lockfile share a release decision (uv and
    # uvx). The backend format repeats that field, so reject inconsistent copies.
    release_versions = {}
    for name, filename, definition in _iter_catalog():
        version = definition.get("version")
        if not isinstance(version, str) or not version:
            raise ValueError(f"Missing native version: {name}")
        if filename in release_versions and release_versions[filename] != version:
            raise ValueError(f"Inconsistent shared release in {filename}")
        release_versions[filename] = version
    for environment in load_environments():
        validate_environment(environment, tools)
    root = LOCKFILE_ROOT.parents[1]
    module = (root / "MODULE.bazel").read_text()
    declared = re.findall(
        r'multitool.hub\(lockfile = "//tools:lockfiles/([^"/]+)"\)', module
    )
    expected = sorted(p.name for p in LOCKFILE_ROOT.glob("*.lock.json"))
    if sorted(declared) != expected:
        raise ValueError("MODULE.bazel native hubs differ from lockfile catalog")
    build = (root / "tools/BUILD.bazel").read_text()
    aliases = re.findall(r'multitool_aliases\("([^"]+)"\)', build)
    native = sorted(
        name for name, data in tools.items() if data["provider"] == "native"
    )
    if sorted(aliases) != native:
        raise ValueError("Bazel aliases differ from native tool catalog")
    for name, data in tools.items():
        if (
            not data.get("description")
            or not data.get("platforms")
            or not data.get("policy")
        ):
            raise ValueError(f"Incomplete inventory definition: {name}")
    dockerfile = root / "src/s-core-devcontainer/.devcontainer/Dockerfile"
    proxyfile = dockerfile.with_name("with-proxy-vars.Dockerfile")
    base = next(
        line for line in dockerfile.read_text().splitlines() if line.startswith("FROM ")
    )
    proxy_base = next(
        line for line in proxyfile.read_text().splitlines() if line.startswith("FROM ")
    )
    if base != proxy_base:
        raise ValueError("Proxy and default Dockerfiles select different base images")
    return tools


def read_jsonc(path):
    """Read Dev Containers JSON with comments while preserving URL/string content."""
    import re

    pattern = r'("(?:\\.|[^"\\])*")|//[^\n]*|/\*.*?\*/'
    return json.loads(
        re.sub(
            pattern,
            lambda match: match.group(1) or "",
            path.read_text(),
            flags=re.DOTALL,
        )
    )


def resolved_provider(name, definition):
    """Resolve external native configuration by reference instead of copying pins."""
    if "config" not in definition:
        return definition
    root = LOCKFILE_ROOT.parents[1]
    config = root / definition["config"]
    result = dict(definition)
    if definition["provider"] == "feature":
        selections = read_jsonc(config)["features"]
        # Reference stable feature identity, leaving requested tags/options with
        # the Dev Containers config rather than copying a major-version pin.
        identity = definition["feature"]
        key = next(
            key
            for key in selections
            if key == identity or key.startswith((identity + ":", identity + "@"))
        )
        settings = selections[key]
        resolution = json.loads(config.with_name("devcontainer-lock.json").read_text())[
            "features"
        ][key]
        request = settings.get(
            "version", key.removeprefix(identity).removeprefix(":") or "bundle"
        )
        result["version"] = str(request) + " / feature " + resolution["version"]
        result["resolution"] = resolution["resolved"]
    elif definition["provider"] == "image":
        if config.suffix == ".json":
            result["version"] = read_jsonc(config)["image"]
        else:
            result["version"] = next(
                line.split(maxsplit=1)[1]
                for line in config.read_text().splitlines()
                if line.startswith("FROM ")
            )
    elif definition["provider"] == "workspace":
        result["version"] = config.read_text().strip()
    return result
