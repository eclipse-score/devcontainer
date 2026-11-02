#!/usr/bin/env python3
# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Build and verify the ordinary Python dependency package from live owners."""

from __future__ import annotations

import argparse
import hashlib
from email.parser import Parser
import json
from pathlib import Path
import re
import shutil
import subprocess
import tomllib
import zipfile

TOOLS_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = TOOLS_ROOT.parent
OWNER_ROOT = TOOLS_ROOT / "mise"
OWNER_FILES = ("mise.native.toml", "mise.python.toml")
VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:(?:a|b|rc)[0-9]+)?(?:\.post[0-9]+)?(?:\.dev[0-9]+)?$"
)
NAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$")


def _owner_configs(owner_root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Read direct package pins from the maintained mise owners."""
    native = tomllib.loads((owner_root / "mise.native.toml").read_text())["tools"]
    python = tomllib.loads((owner_root / "mise.python.toml").read_text())["tools"]
    if not all(
        isinstance(key, str) and isinstance(value, str) for key, value in native.items()
    ):
        raise SystemExit("mise.native.toml must contain string tool pins")
    if not all(
        isinstance(key, str) and isinstance(value, str) for key, value in python.items()
    ):
        raise SystemExit("mise.python.toml must contain string tool pins")
    return native, python


def _python_catalog() -> dict[str, dict[str, str]]:
    """Read package and extra names from the data-only compatibility catalog."""
    import sys

    sys.path.insert(0, str(TOOLS_ROOT))
    from score_tools.catalog import _load_python_tools

    return _load_python_tools()


def _project_metadata(version: str, package_name: str, owner_root: Path) -> dict:
    if not VERSION_PATTERN.fullmatch(version):
        raise SystemExit(
            f"Release version must be explicit PEP 440 version: {version!r}"
        )
    if not NAME_PATTERN.fullmatch(package_name):
        raise SystemExit(f"Invalid Python package name: {package_name!r}")

    native, python = _owner_configs(owner_root)
    catalog = _python_catalog()
    requires_python = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]["requires-python"]
    if not isinstance(requires_python, str) or not requires_python:
        raise SystemExit("Root pyproject.toml must declare project.requires-python")
    extras: dict[str, list[str]] = {}
    selected: dict[str, str] = {}

    ruff_backend = "aqua:astral-sh/ruff"
    if ruff_backend not in native:
        raise SystemExit(f"Missing direct mise owner pin for {ruff_backend}")
    extras["ruff"] = ["ruff==" + native[ruff_backend]]
    selected["ruff"] = native[ruff_backend]

    for command, metadata in sorted(catalog.items()):
        backend = "pypi:" + metadata["package"]
        if backend not in python:
            raise SystemExit(f"Missing direct mise owner pin for {backend}")
        if command in extras:
            raise SystemExit(f"Duplicate Python dependency extra: {command}")
        extras[command] = [metadata["package"] + "==" + python[backend]]
        selected[command] = python[backend]

    source_hashes = {
        filename: hashlib.sha256((owner_root / filename).read_bytes()).hexdigest()
        for filename in OWNER_FILES
    }
    return {
        "name": package_name,
        "version": version,
        "requires_python": requires_python,
        "extras": extras,
        "selected_tool_versions": selected,
        "owner_sha256": source_hashes,
    }


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def render_pyproject(metadata: dict) -> str:
    """Render static PEP 621 metadata so uv and pip need no SCORE runner."""
    lines = [
        "[build-system]",
        'requires = ["setuptools>=68"]',
        'build-backend = "setuptools.build_meta"',
        "",
        "[project]",
        "name = " + _toml_string(metadata["name"]),
        "version = " + _toml_string(metadata["version"]),
        'description = "Pinned Python dependencies selected by the SCORE tool owners"',
        "requires-python = " + _toml_string(metadata["requires_python"]),
        "",
        "[project.optional-dependencies]",
    ]
    lines.extend(
        _toml_string(extra) + " = [" + ", ".join(map(_toml_string, requirements)) + "]"
        for extra, requirements in metadata["extras"].items()
    )
    lines.extend(["", "[tool.setuptools]", "packages = []", ""])
    return "\n".join(lines)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _verify_wheel(path: Path, metadata: dict) -> None:
    try:
        with zipfile.ZipFile(path) as wheel:
            metadata_paths = [
                member
                for member in wheel.namelist()
                if member.endswith(".dist-info/METADATA")
            ]
            if len(metadata_paths) != 1:
                raise SystemExit(f"Expected one wheel METADATA file in {path}")
            parsed = Parser().parsestr(wheel.read(metadata_paths[0]).decode("utf-8"))
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError) as exc:
        raise SystemExit(f"Cannot inspect dependency wheel {path}: {exc}") from exc

    if _canonical_name(parsed.get("Name", "")) != _canonical_name(metadata["name"]):
        raise SystemExit(f"Wheel package name does not match release metadata: {path}")
    if parsed.get("Version") != metadata["version"]:
        raise SystemExit(f"Wheel version does not match release metadata: {path}")
    if parsed.get("Requires-Python") != metadata["requires_python"]:
        raise SystemExit(
            f"Wheel Python requirement does not match release metadata: {path}"
        )
    declared_extras = set(parsed.get_all("Provides-Extra", []))
    if declared_extras != set(metadata["extras"]):
        raise SystemExit(f"Wheel extras do not match current owners: {path}")

    dependencies = parsed.get_all("Requires-Dist", [])
    for extra, requirements in metadata["extras"].items():
        for requirement in requirements:
            prefix = requirement.lower() + "; extra == "
            matching = [
                value.lower()
                for value in dependencies
                if value.lower().startswith(prefix)
            ]
            if len(matching) != 1 or f'"{extra.lower()}"' not in matching[0]:
                raise SystemExit(
                    f"Wheel is missing owner-pinned dependency {requirement!r} "
                    f"in extra {extra!r}"
                )


def build_release(
    destination: Path,
    version: str,
    package_name: str,
    owner_root: Path = OWNER_ROOT,
    uv: str | None = None,
) -> Path:
    """Build one local wheel and bind it to exact owners and release identity."""
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit(f"Release destination must be empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    metadata = _project_metadata(version, package_name, owner_root)
    (destination / "pyproject.toml").write_text(render_pyproject(metadata))

    uv_binary = uv or shutil.which("uv")
    if not uv_binary:
        raise SystemExit("uv is required to build the local dependency wheel")
    dist = destination / "dist"
    dist.mkdir(exist_ok=True)
    subprocess.run(
        [uv_binary, "build", "--wheel", "--out-dir", str(dist)],
        cwd=destination,
        check=True,
    )
    wheels = sorted(dist.glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"Expected one built wheel, found {len(wheels)} in {dist}")
    _verify_wheel(wheels[0], metadata)

    manifest = {
        "schema_version": 1,
        **metadata,
        "wheel": {
            "path": wheels[0].relative_to(destination).as_posix(),
            "sha256": _sha256(wheels[0]),
        },
    }
    (destination / "release.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    return wheels[0]


def check_release(release: Path, owner_root: Path = OWNER_ROOT) -> None:
    """Check release identity, generated metadata, owner pins, and wheel bytes."""
    try:
        manifest = json.loads((release / "release.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read local package release metadata: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise SystemExit("Unsupported Python dependency release metadata")
    expected = _project_metadata(
        manifest.get("version", ""), manifest.get("name", ""), owner_root
    )
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise SystemExit(
                f"Local release is stale for {key}; rebuild from current owners"
            )
    project = release / "pyproject.toml"
    if not project.is_file() or project.read_text() != render_pyproject(expected):
        raise SystemExit(
            "Local release pyproject.toml does not match its bound metadata"
        )
    wheel_record = manifest.get("wheel")
    if not isinstance(wheel_record, dict) or not isinstance(
        wheel_record.get("path"), str
    ):
        raise SystemExit("Local release is missing its wheel record")
    wheel = (release / wheel_record["path"]).resolve()
    if release.resolve() not in wheel.parents or not wheel.is_file():
        raise SystemExit("Local release wheel path is missing or escapes its release")
    if _sha256(wheel) != wheel_record.get("sha256"):
        raise SystemExit("Local release wheel digest does not match release.json")
    _verify_wheel(wheel, expected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    build = subparsers.add_parser(
        "build", help="build a local ordinary dependency wheel"
    )
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--version", required=True)
    build.add_argument("--package-name", required=True)
    build.add_argument("--owner-root", type=Path, default=OWNER_ROOT)
    build.add_argument("--uv")
    check = subparsers.add_parser(
        "check", help="verify a local package against current owners"
    )
    check.add_argument("release", type=Path)
    check.add_argument("--owner-root", type=Path, default=OWNER_ROOT)
    args = parser.parse_args()
    if args.action == "build":
        wheel = build_release(
            args.output.resolve(),
            args.version,
            args.package_name,
            args.owner_root.resolve(),
            args.uv,
        )
        print(wheel)
    else:
        check_release(args.release.resolve(), args.owner_root.resolve())
        print("Local dependency release matches current owners")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
