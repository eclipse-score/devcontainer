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
"""Check existing feature scripts can consume the shared package definitions."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.internal.devcontainer import install as installer

TOOLS_DIR = Path(__file__).resolve().parents[1]


class MetadataTest(unittest.TestCase):
    def test_every_feature_version_and_checksum_input_is_exported(self) -> None:
        # Removing the YAML loader must not leave an install or test command with
        # an undefined version/checksum variable, even in an architecture branch.
        metadata = installer._metadata_values()
        for feature in ("s-core-local", "bazel-feature"):
            for script in ("install.sh", "tests/test_default.sh"):
                path = (
                    TOOLS_DIR.parent
                    / "src/s-core-devcontainer/.devcontainer"
                    / feature
                    / script
                )
                required = set(
                    re.findall(
                        r"\$\{([A-Za-z_][A-Za-z_0-9]*(?:_version|_sha256))(?:[^}]*)?\}",
                        path.read_text(),
                    )
                )
                with self.subTest(script=path):
                    self.assertTrue(required)
                    self.assertFalse(
                        required - metadata.keys(), required - metadata.keys()
                    )

    def test_shell_metadata_keeps_command_substitution_as_literal_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = self._copy_tools(root)
            marker = root / "must-not-exist"
            value = "$(touch " + str(marker) + ") 'quoted value'"
            providers = {"fixture": {"provider": "release", "version": value}}
            (tools / "providers.json").write_text(json.dumps(providers))
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(tools / "internal/devcontainer/install.py"),
                    "shell-metadata",
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            check = subprocess.run(
                [
                    "bash",
                    "-c",
                    'eval "$1"; test "$fixture_version" = "$2"',
                    "metadata-test",
                    result.stdout,
                    value,
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertFalse(marker.exists())

    def _copy_tools(self, root: Path) -> Path:
        tools = root / "copied-tools"
        shutil.copytree(TOOLS_DIR, tools, ignore=shutil.ignore_patterns("__pycache__"))
        return tools


if __name__ == "__main__":
    unittest.main()
