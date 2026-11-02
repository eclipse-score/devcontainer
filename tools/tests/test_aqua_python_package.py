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
"""Keep ordinary Python dependency metadata bound to maintained tool owners."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "internal/aqua"))
from python_package import package_metadata, selected_versions


OWNER_DIR = Path(__file__).resolve().parents[1] / "owners/aqua"


class AquaPythonPackageTest(unittest.TestCase):
    def test_metadata_uses_explicit_identity_and_owner_versions(self):
        """The wheel metadata takes its name/version from inputs and pins from owners."""
        metadata = package_metadata(OWNER_DIR, "9.8.7", "candidate-local-name")

        self.assertIn('name = "candidate-local-name"', metadata)
        self.assertIn('version = "9.8.7"', metadata)
        self.assertIn('"repository" = ["pre-commit==4.7.0", "ruff==0.11.12"]', metadata)
        self.assertIn(
            '"published" = ["pre-commit==4.7.0", "pytest==9.0.2", "basedpyright==1.35.0", "codespell==2.4.1", "ruff==0.11.12"]',
            metadata,
        )

    def test_release_selection_includes_native_and_python_owner_versions(self):
        """Release metadata binds the complete selected profile from both owners."""
        selected = selected_versions(OWNER_DIR)

        self.assertEqual(selected["repository"]["uv"], "0.13.6")
        self.assertEqual(selected["repository"]["ruff"], "0.11.12")
        self.assertEqual(selected["published"]["apm"], "0.35.0")
        self.assertEqual(selected["published"]["basedpyright"], "1.35.0")

    def test_invalid_distribution_identity_is_rejected(self):
        """Local identities must still be valid Python distribution names."""
        with self.assertRaisesRegex(ValueError, "Invalid Python distribution name"):
            package_metadata(OWNER_DIR, "0.1.0", "candidate/name")


if __name__ == "__main__":
    unittest.main()
