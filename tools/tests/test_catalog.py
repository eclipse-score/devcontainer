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
"""Contract checks for catalog ownership and standalone process boundaries."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_tools import catalog


class CatalogTest(unittest.TestCase):
    def test_current_compositions_and_bazel_registrations_are_consistent(self):
        catalog.validate_catalog()

    def test_undefined_environment_member_fails(self):
        with (
            patch.object(
                catalog,
                "load_environments",
                return_value={"image": {"native": ["typo"]}},
            ),
            self.assertRaisesRegex(ValueError, "Undefined tool typo"),
        ):
            catalog.validate_catalog()

    def test_duplicate_environment_member_fails(self):
        with (
            patch.object(
                catalog,
                "load_environments",
                return_value={"image": {"native": ["uv", "uv"]}},
            ),
            self.assertRaisesRegex(ValueError, "Duplicate selection"),
        ):
            catalog.validate_catalog()

    def test_provider_mismatch_fails_before_installation(self):
        with (
            patch.object(
                catalog, "load_environments", return_value={"image": {"apt": ["uv"]}}
            ),
            self.assertRaisesRegex(ValueError, "Wrong provider"),
        ):
            catalog.validate_catalog()

    def test_python_catalog_rejects_executable_content(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.bzl"
            path.write_text('PYTHON_TOOLS = {}\nraise RuntimeError("executed")\n')
            with (
                patch.object(catalog, "PYTHON_TOOL_CATALOG", path),
                self.assertRaisesRegex(SystemExit, "only a PYTHON_TOOLS assignment"),
            ):
                catalog._load_python_tools()

    def test_apt_requests_distinguish_prefix_distribution_and_package_name(self):
        requirements = catalog.apt_requirements("s-core-local")
        self.assertIn("git", requirements)
        self.assertIn("valgrind=1:3.22.0*", requirements)
        self.assertIn("python3.12", requirements)
        self.assertNotIn("python3.12=3.12*", requirements)

    def test_qemu_excludes_recommendations_without_affecting_python_build_support(self):
        without_recommends = catalog.apt_requirements("s-core-local", recommends=False)
        self.assertEqual(
            without_recommends, ["qemu-system-arm=1:8.2.2*", "qemu-system-x86=1:8.2.2*"]
        )
        normal = catalog.apt_requirements("s-core-local", recommends=True)
        self.assertIn("python3-pip", normal)
        self.assertFalse(any(item.startswith("qemu-system") for item in normal))

    def test_environment_removal_changes_apt_request(self):
        selections = catalog.load_environments()
        selections["s-core-local"]["apt"].remove("graphviz")
        with patch.object(catalog, "load_environments", return_value=selections):
            self.assertFalse(
                any(
                    item.startswith("graphviz")
                    for item in catalog.apt_requirements("s-core-local")
                )
            )

    def test_jsonc_comments_do_not_corrupt_urls_or_quoted_slashes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                '{// comment\n"url":"https://host/path/*literal*/",/* block */"value": "//quoted"}'
            )
            self.assertEqual(
                catalog.read_jsonc(path)["url"], "https://host/path/*literal*/"
            )


class InstalledResultTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util

        path = Path(__file__).resolve().parents[1] / "internal/devcontainer/install.py"
        spec = importlib.util.spec_from_file_location("score_container_installer", path)
        cls.installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.installer)

    def test_shell_metadata_quotes_values_and_ignores_inventory_only_keys(self):
        import argparse
        import io
        from contextlib import redirect_stdout

        output = io.StringIO()
        value = 'literal spaces $(false); "quoted"'
        providers = {
            "tool": {"version": value, "omissions": {"linux/arm64": "intentional"}}
        }
        with (
            patch.object(self.installer, "load_providers", return_value=providers),
            patch.object(self.installer, "_load_python_tools", return_value={}),
            redirect_stdout(output),
        ):
            self.installer._cmd_shell_metadata(argparse.Namespace())
        self.assertNotIn("omissions", output.getvalue())
        run = subprocess.run(
            ["bash", "-c", output.getvalue() + 'printf %s "$tool_version"'],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(run.stdout, value)

    def test_installed_native_version_drift_is_rejected(self):
        # A successful command is insufficient: the installed release must match.
        import argparse

        selection = {"image": {"native": ["uv"], "python": []}}
        with (
            patch.object(self.installer, "load_environments", return_value=selection),
            patch.object(self.installer.shutil, "which", return_value="/test/uv"),
            patch.object(
                self.installer.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0, "uv 999.0.0"),
            ),
            self.assertRaisesRegex(SystemExit, "Unexpected uv version"),
        ):
            self.installer._cmd_verify_environment(
                argparse.Namespace(environment="image")
            )

    def test_nonroot_missing_command_is_rejected(self):
        import argparse

        selection = {"image": {"native": [], "python": ["pre-commit"]}}
        with (
            patch.object(self.installer, "load_environments", return_value=selection),
            patch.object(self.installer.shutil, "which", return_value=None),
            self.assertRaisesRegex(SystemExit, "Selected command missing"),
        ):
            self.installer._cmd_verify_environment(
                argparse.Namespace(environment="image")
            )

    def test_installed_apt_prefix_drift_is_rejected(self):
        import argparse

        selection = {"image": {"native": [], "python": [], "apt": ["graphviz"]}}
        with (
            patch.object(self.installer, "load_environments", return_value=selection),
            patch.object(self.installer.shutil, "which", return_value="/test/dot"),
            patch.object(
                self.installer.subprocess,
                "run",
                return_value=subprocess.CompletedProcess(
                    [], 0, "install ok installed\n999.0"
                ),
            ),
            self.assertRaisesRegex(SystemExit, "Unexpected graphviz version"),
        ):
            self.installer._cmd_verify_environment(
                argparse.Namespace(environment="image")
            )


class StandaloneTest(unittest.TestCase):
    def test_uv_receives_catalog_selection_cwd_arguments_and_propagates_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            uv = directory / "uv"
            uv.write_text(
                "#!" + sys.executable + "\nimport json, os, sys\n"
                "print(json.dumps([os.getcwd(), sys.argv[1:]]))\nsys.exit(37)\n"
            )
            uv.chmod(0o755)
            environment = {
                **os.environ,
                "PATH": str(directory),
                "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
            }
            run = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from score_tools.cli import main; raise SystemExit(main())",
                    "pre-commit",
                    "run",
                    "a b",
                    "",
                    "$(echo unsafe)",
                ],
                cwd=directory,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(run.returncode, 37, run.stderr)
            tool = catalog._load_python_tools()["pre-commit"]
            self.assertEqual(
                json.loads(run.stdout),
                [
                    str(directory),
                    [
                        "tool",
                        "run",
                        "--from",
                        tool["package"] + "==" + tool["version"],
                        tool["entrypoint"],
                        "run",
                        "a b",
                        "",
                        "$(echo unsafe)",
                    ],
                ],
            )

    def test_unknown_tool_does_not_fall_back_to_unpinned_uv(self):
        with patch("sys.argv", ["score-tool", "typo"]):
            from score_tools.cli import main

            self.assertEqual(main(), 2)


if __name__ == "__main__":
    unittest.main()
