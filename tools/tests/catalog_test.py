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
"""Regression coverage for the shared catalog and its script consumers."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.internal import catalog


TOOLS_DIR = Path(__file__).resolve().parents[1]


class CatalogTest(unittest.TestCase):
    def test_metadata_matches_definitions(self) -> None:
        versions = {}
        descriptions = {}
        for path in sorted((TOOLS_DIR / "lockfiles").glob("*.lock.json")):
            for name, metadata in json.loads(path.read_text(encoding="utf-8")).items():
                if name.startswith("$"):
                    continue
                with self.subTest(tool=name):
                    self.assertEqual(
                        catalog.load_tool(path.name.removesuffix(".lock.json"), name),
                        metadata,
                    )
                versions[name] = metadata["version"]
                if "description" in metadata:
                    descriptions[name] = metadata["description"]

        providers = json.loads((TOOLS_DIR / "providers.json").read_text())
        python_tools = {
            name: {
                field: definition[field]
                for field in ("package", "version", "entrypoint", "description")
            }
            for name, definition in providers.items()
            if definition["provider"] == "python"
        }
        self.assertEqual(catalog.load_python_tools(), python_tools)
        self.assertEqual(set(python_tools), {"pre-commit", "basedpyright", "pytest"})
        versions.update(
            (name, metadata["version"]) for name, metadata in python_tools.items()
        )
        descriptions.update(
            (name, metadata["description"]) for name, metadata in python_tools.items()
        )
        self.assertEqual(catalog.load_catalog_versions(), versions)
        self.assertEqual(catalog.load_catalog_descriptions(), descriptions)
        self.assertEqual(catalog.resolve_lockfile("uvx"), "uv")
        self.assertEqual(catalog.resolve_lockfile("uvx", "explicit"), "explicit")

    def test_rejects_python_packages_with_missing_fields_or_uv_dependency(self) -> None:
        valid = {
            "provider": "python",
            "package": "example",
            "version": "1",
            "entrypoint": "example",
            "description": "Example tool",
            "requires": ["uv"],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "providers.json"
            with patch.object(catalog, "PROVIDERS_PATH", path):
                for field in (
                    "package",
                    "version",
                    "entrypoint",
                    "description",
                    "requires",
                ):
                    with self.subTest(field=field):
                        definition = {
                            key: value for key, value in valid.items() if key != field
                        }
                        path.write_text(json.dumps({"example": definition}))
                        message = (
                            "uv dependency"
                            if field == "requires"
                            else "Malformed Python package definition"
                        )
                        with self.assertRaisesRegex(SystemExit, message):
                            catalog.load_python_tools()

    def test_duplicate_definitions_retain_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            python_path = root / "providers.json"
            metadata = {
                "version": "1",
                "description": "Example tool",
                "binaries": [],
            }
            native_path = root / "one.lock.json"
            native_path.write_text(json.dumps({"example": metadata}), encoding="utf-8")
            duplicate_path = root / "two.lock.json"
            python_metadata = {
                "provider": "python",
                "requires": ["uv"],
                "package": "example",
                "version": "1",
                "entrypoint": "example",
                "description": "Example tool",
            }
            with (
                patch.object(catalog, "LOCKFILE_ROOT", root),
                patch.object(catalog, "PROVIDERS_PATH", python_path),
            ):
                for duplicate in ("lockfiles", "catalogs"):
                    if duplicate == "lockfiles":
                        duplicate_path.write_bytes(native_path.read_bytes())
                        python_path.write_text("{}", encoding="utf-8")
                    else:
                        duplicate_path.unlink()
                        python_path.write_text(
                            json.dumps({"example": python_metadata}),
                            encoding="utf-8",
                        )
                    for query in (
                        catalog.load_catalog_versions,
                        catalog.load_catalog_descriptions,
                    ):
                        with self.subTest(duplicate=duplicate, query=query.__name__):
                            with self.assertRaisesRegex(
                                SystemExit,
                                f"Tool 'example' is defined by multiple {duplicate}",
                            ):
                                query()

    def test_copied_scripts_work_without_installer_import_for_readme(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copied = root / "tools"
            shutil.copytree(
                TOOLS_DIR, copied, ignore=shutil.ignore_patterns("__pycache__")
            )
            readme = copied / "README.md"
            expected = readme.read_bytes()
            # Force regeneration, rather than only testing the no-change path.
            readme.write_text(
                expected.decode("utf-8").replace(
                    "| `pre-commit` |", "| `stale-command` |"
                ),
                encoding="utf-8",
            )
            blocker = """
import importlib.abc
import runpy
import sys

class BlockInstaller(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if "devcontainer" in fullname.split("."):
            raise AssertionError("README generation imported the container installer")

sys.meta_path.insert(0, BlockInstaller())
script = sys.argv[1]
sys.argv = [script]
runpy.run_path(script, run_name="__main__")
"""
            subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    "-c",
                    blocker,
                    str(copied / "internal/sync_readme.py"),
                ],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(readme.read_bytes(), expected)
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(copied / "internal/devcontainer/install.py"),
                    "version",
                    "pre-commit",
                ],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                result.stdout.strip(),
                catalog.load_python_tools()["pre-commit"]["version"],
            )


if __name__ == "__main__":
    unittest.main()
