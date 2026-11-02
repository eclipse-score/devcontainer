# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Ordinary dependency metadata, stale-owner and wheel binding regressions."""

import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location(
    "dependency_package",
    Path(__file__).resolve().parents[1] / "internal/dependency_package.py",
)
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class DependencyPackageTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.owners = self.root / "tools"
        shutil.copytree(package.TOOLS_ROOT / "lockfiles", self.owners / "lockfiles")
        (self.owners / "score_tools").mkdir()
        shutil.copyfile(
            package.TOOLS_ROOT / "score_tools/python_tools.bzl",
            self.owners / "score_tools/python_tools.bzl",
        )
        shutil.copyfile(
            package.TOOLS_ROOT / "environments.json", self.owners / "environments.json"
        )
        self.release = self.root / "release"
        self.release.mkdir()
        self.data = package.metadata(self.owners, "0.8.0", "score-own-test-local")
        (self.release / "pyproject.toml").write_text(package.render(self.data))
        self.wheel = self.release / "fixture.whl"
        fields = [
            "Metadata-Version: 2.4",
            "Name: " + self.data["name"],
            "Version: " + self.data["version"],
            "Requires-Python: " + self.data["requires_python"],
        ]
        for extra, requirements in self.data["extras"].items():
            fields.append("Provides-Extra: " + extra)
            fields.extend(
                f'Requires-Dist: {requirement}; extra == "{extra}"'
                for requirement in requirements
            )
        self.fields = fields
        self.write_wheel()

    def write_wheel(self):
        with zipfile.ZipFile(self.wheel, "w") as archive:
            archive.writestr(
                "fixture.dist-info/METADATA", "\n".join(self.fields) + "\n"
            )
        record = {
            "schema": 1,
            **self.data,
            "wheel": self.wheel.name,
            "sha256": package.digest(self.wheel),
        }
        (self.release / "release.json").write_text(json.dumps(record))

    def test_exact_owner_requirements_without_runner_or_runtime_payload(self):
        package.check(self.release, self.owners)
        self.assertIn("ruff==", self.data["extras"]["ruff"][0])
        self.assertNotIn("scripts", package.render(self.data))

    def test_stale_generated_pyproject_rejected(self):
        (self.release / "pyproject.toml").write_text("stale")
        with self.assertRaisesRegex(ValueError, "Stale generated"):
            package.check(self.release, self.owners)

    def test_release_a_rejected_against_changed_owner_b(self):
        path = self.owners / "score_tools/python_tools.bzl"
        path.write_text(path.read_text().replace('"4.7.0"', '"4.7.1"'))
        with self.assertRaisesRegex(ValueError, "Stale dependency release"):
            package.check(self.release, self.owners)

    def test_changed_wheel_bytes_rejected(self):
        with self.wheel.open("ab") as output:
            output.write(b"changed")
        with self.assertRaisesRegex(ValueError, "digest"):
            package.check(self.release, self.owners)

    def test_extra_unowned_dependency_rejected_even_with_updated_wheel_hash(self):
        self.fields.append("Requires-Dist: unwanted==1.0")
        self.write_wheel()
        with self.assertRaisesRegex(ValueError, "dependencies differ"):
            package.check(self.release, self.owners)

    def test_removed_python_tool_no_longer_offered_in_new_dependency_metadata(self):
        path = self.owners / "score_tools/python_tools.bzl"
        path.write_text("PYTHON_TOOLS = {}\n")
        generated = package.metadata(self.owners, "0.8.1", "score-own-test-local")
        self.assertEqual(set(generated["extras"]), {"ruff", "all"})

    def test_invalid_identity_and_implicit_version_rejected(self):
        for version, name in (("latest", "valid"), ("1.0.0", "../invalid")):
            with self.assertRaises(ValueError):
                package.metadata(self.owners, version, name)

    def test_removed_ruff_is_not_offered_by_new_dependency_release(self):
        (self.owners / "lockfiles/ruff.lock.json").unlink()
        generated = package.metadata(self.owners, "0.8.1", "score-own-test-local")
        self.assertNotIn("ruff", generated["extras"])


if __name__ == "__main__":
    unittest.main()
