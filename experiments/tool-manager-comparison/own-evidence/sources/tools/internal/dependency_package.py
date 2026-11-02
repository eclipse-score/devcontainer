#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Build/check an ordinary dependency wheel bound to the portable tool owners."""

from __future__ import annotations

import argparse
from email.parser import Parser
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_tools.catalog import _load_python_tools, load_native_tools

TOOLS_ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def metadata(root: Path, version: str, name: str) -> dict:
    if not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+(?:(?:a|b|rc)[0-9]+)?(?:\.post[0-9]+)?(?:\.dev[0-9]+)?",
        version,
    ):
        raise ValueError(f"Explicit release version required (e.g. 1.2.3): {version!r}")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?", name):
        raise ValueError(f"Invalid package identity: {name!r}")
    python = _load_python_tools(root / "score_tools/python_tools.bzl")
    native = load_native_tools(root)
    if "ruff" in python:
        raise ValueError("Ruff must have one owner, not native and Python copies")
    extras = (
        {"ruff": ["ruff==" + native["ruff"]["version"]]} if "ruff" in native else {}
    )
    extras.update(
        {
            command: [data["package"] + "==" + data["version"]]
            for command, data in sorted(python.items())
        }
    )
    extras["all"] = sorted(
        {
            requirement
            for requirements in extras.values()
            for requirement in requirements
        }
    )
    owners = [
        *sorted((root / "lockfiles").glob("*.lock.json")),
        root / "score_tools/python_tools.bzl",
        root / "environments.json",
    ]
    return {
        "name": name,
        "version": version,
        "requires_python": ">=3.11",
        "extras": extras,
        "owners": {str(path.relative_to(root)): digest(path) for path in owners},
    }


def render(data: dict) -> str:
    return "\n".join(
        [
            "[build-system]",
            'requires = ["setuptools>=68"]',
            'build-backend = "setuptools.build_meta"',
            "",
            "[project]",
            "name = " + json.dumps(data["name"]),
            "version = " + json.dumps(data["version"]),
            'description = "Release-selected SCORE Python tool dependencies"',
            "requires-python = " + json.dumps(data["requires_python"]),
            "",
            "[project.optional-dependencies]",
            *[
                json.dumps(extra) + " = " + json.dumps(requirements)
                for extra, requirements in data["extras"].items()
            ],
            "",
            "[tool.setuptools]",
            "packages = []",
            "",
        ]
    )


def verify_wheel(wheel: Path, data: dict) -> None:
    with zipfile.ZipFile(wheel) as archive:
        paths = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(paths) != 1:
            raise ValueError("Wheel must contain exactly one METADATA")
        parsed = Parser().parsestr(archive.read(paths[0]).decode())

    def canonical(name):
        return re.sub(r"[-_.]+", "-", name).lower()

    if (
        canonical(parsed.get("Name", "")) != canonical(data["name"])
        or parsed.get("Version") != data["version"]
    ):
        raise ValueError("Wheel identity differs from release")
    if parsed.get("Requires-Python") != data["requires_python"]:
        raise ValueError("Wheel Python requirement differs from release")
    if set(parsed.get_all("Provides-Extra", [])) != set(data["extras"]):
        raise ValueError("Wheel extras differ from owners")
    expected = {
        f'{requirement};extra=="{extra}"'.lower()
        for extra, requirements in data["extras"].items()
        for requirement in requirements
    }
    actual = {
        value.replace(" ", "").lower() for value in parsed.get_all("Requires-Dist", [])
    }
    if actual != expected:
        raise ValueError(f"Wheel dependencies differ from owners: {actual ^ expected}")


def build(output: Path, root: Path, version: str, name: str, uv: str) -> Path:
    data = metadata(root, version, name)
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Release destination must be empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "pyproject.toml").write_text(render(data))
    subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(output / "dist")],
        cwd=output,
        check=True,
    )
    wheels = list((output / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise ValueError("Expected exactly one built wheel")
    verify_wheel(wheels[0], data)
    record = {
        "schema": 1,
        **data,
        "wheel": str(wheels[0].relative_to(output)),
        "sha256": digest(wheels[0]),
    }
    (output / "release.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n"
    )
    check(output, root)
    return wheels[0]


def check(release: Path, root: Path) -> None:
    data = json.loads((release / "release.json").read_text())
    if data.get("schema") != 1:
        raise ValueError("Unsupported dependency release schema")
    expected = metadata(root, data["version"], data["name"])
    if any(data.get(key) != value for key, value in expected.items()):
        raise ValueError("Stale dependency release: owners/identity differ; rebuild")
    if (release / "pyproject.toml").read_text() != render(expected):
        raise ValueError("Stale generated dependency metadata; rebuild")
    wheel = (release / data["wheel"]).resolve()
    if not wheel.is_relative_to(release.resolve()) or digest(wheel) != data["sha256"]:
        raise ValueError("Wheel path/digest differs from bound release")
    verify_wheel(wheel, expected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    build_parser = actions.add_parser("build")
    build_parser.add_argument("--output", type=Path, required=True)
    build_parser.add_argument("--version", required=True)
    build_parser.add_argument("--package-name", required=True)
    build_parser.add_argument("--uv", default=shutil.which("uv") or "uv")
    check_parser = actions.add_parser("check")
    check_parser.add_argument("release", type=Path)
    for action in (build_parser, check_parser):
        action.add_argument("--catalog-root", type=Path, default=TOOLS_ROOT)
    args = parser.parse_args()
    try:
        if args.action == "build":
            print(
                build(
                    args.output.resolve(),
                    args.catalog_root.resolve(),
                    args.version,
                    args.package_name,
                    args.uv,
                )
            )
        else:
            check(args.release.resolve(), args.catalog_root.resolve())
            print("Dependency release matches current owners")
    except (
        ValueError,
        KeyError,
        OSError,
        zipfile.BadZipFile,
        subprocess.CalledProcessError,
    ) as exc:
        parser.exit(1, f"Dependency release failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
