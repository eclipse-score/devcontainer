# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Check ordinary package extras derive from maintained version owners."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT))
spec = importlib.util.spec_from_file_location(
    "score_mise_python_package", TOOLS_ROOT / "internal/mise/python_package.py"
)
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PythonPackageMetadataTest(unittest.TestCase):
    def test_stale_native_lock_is_rejected_even_with_python_optimization(self):
        """An owner edit must not export new versions with old artifact bytes."""
        refresh = TOOLS_ROOT / "internal/mise/refresh.py"
        script = (
            "import pathlib, runpy, sys; "
            "refresh = runpy.run_path(sys.argv[1]); "
            "refresh['export_native'](pathlib.Path(sys.argv[2]), "
            "{'aqua:astral-sh/ruff': '0.14.6'}, "
            "{'aqua:astral-sh/ruff': 'ruff'})"
        )
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "mise.native.lock").write_text(
                '[[tools."aqua:astral-sh/ruff"]]\nversion = "0.11.13"\n'
            )
            for flags in ([], ["-O"]):
                with self.subTest(flags=flags):
                    result = subprocess.run(
                        [sys.executable, *flags, "-c", script, str(refresh), directory],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Stale mise artifact lock", result.stderr)
                    self.assertIn("owner=0.14.6, lock=0.11.13", result.stderr)
                    self.assertIn("tools/internal/mise/refresh.sh", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_explicit_identity_and_all_extras_bind_to_direct_owner_pins(self):
        metadata = package._project_metadata(
            "0.6.1", "score-local-candidate", package.OWNER_ROOT
        )
        native, python = package._owner_configs(package.OWNER_ROOT)

        self.assertEqual(metadata["name"], "score-local-candidate")
        self.assertEqual(metadata["version"], "0.6.1")
        self.assertEqual(metadata["requires_python"], ">=3.11")
        self.assertEqual(
            metadata["extras"]["ruff"], ["ruff==" + native["aqua:astral-sh/ruff"]]
        )
        self.assertEqual(
            metadata["extras"]["pre-commit"],
            ["pre-commit==" + python["pypi:pre-commit"]],
        )
        self.assertEqual(
            metadata["selected_tool_versions"]["codespell"],
            python["pypi:codespell"],
        )
        self.assertEqual(
            set(metadata["extras"]),
            {"ruff", "pre-commit", "basedpyright", "pytest", "codespell"},
        )

    def test_release_version_is_required_to_be_a_concrete_version(self):
        for version in ("", "latest", "1.0"):
            with (
                self.subTest(version=version),
                self.assertRaisesRegex(SystemExit, "Release version must be explicit"),
            ):
                package._project_metadata(
                    version, "score-local-candidate", package.OWNER_ROOT
                )

    def test_production_exporter_does_not_reference_experiments(self):
        refresh = TOOLS_ROOT / "internal/mise/refresh.py"
        self.assertNotIn("experiments", refresh.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
