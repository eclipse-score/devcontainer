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
"""Version updates must refresh versioned assets or fail without writing drift."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "internal/refresh_lockfile_digests.py"
spec = importlib.util.spec_from_file_location("refresh", path)
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


class RefreshTest(unittest.TestCase):
    def test_single_version_edit_updates_tag_filename_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tool.lock.json"
            path.write_text(
                json.dumps(
                    {
                        "tool": {
                            "version": "2.0.0",
                            "binaries": [
                                {
                                    "url": "https://github.com/example/tool/releases/download/v1.0.0/tool-1.0.0.tar.gz",
                                    "sha256": "old",
                                }
                            ],
                        }
                    }
                )
            )
            with patch.object(
                refresh,
                "_release_digests",
                return_value={"tool-2.0.0.tar.gz": "sha256:new"},
            ):
                refresh.refresh_lockfile(path)
            binary = json.loads(path.read_text())["tool"]["binaries"][0]
            self.assertEqual(
                binary["url"],
                "https://github.com/example/tool/releases/download/v2.0.0/tool-2.0.0.tar.gz",
            )
            self.assertEqual(binary["sha256"], "new")

    def test_version_edit_updates_versioned_archive_member_and_directory(self):
        """The installer must extract from the new release, not its old layout."""
        for archive_field, old_path in (
            ("file", "tool-v1.0.0/tool"),
            ("dir", "tool-1.0.0/"),
        ):
            with (
                self.subTest(archive_field=archive_field),
                tempfile.TemporaryDirectory() as directory,
            ):
                path = Path(directory) / "tool.lock.json"
                path.write_text(
                    json.dumps(
                        {
                            "tool": {
                                "version": "2.0.0",
                                "binaries": [
                                    {
                                        "url": "https://github.com/example/tool/releases/download/v1.0.0/tool-1.0.0.tar.gz",
                                        "sha256": "old",
                                        archive_field: old_path,
                                    }
                                ],
                            }
                        }
                    )
                )
                with patch.object(
                    refresh,
                    "_release_digests",
                    return_value={"tool-2.0.0.tar.gz": "sha256:new"},
                ):
                    refresh.refresh_lockfile(path)
                binary = json.loads(path.read_text())["tool"]["binaries"][0]
                self.assertEqual(
                    binary[archive_field], old_path.replace("1.0.0", "2.0.0")
                )

    def test_sibling_command_version_is_derived_from_release_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tool.lock.json"
            binary = {
                "url": "https://github.com/example/tool/releases/download/v1.0.0/tool.tar.gz",
                "sha256": "old",
            }
            path.write_text(
                json.dumps(
                    {
                        "tool": {"version": "2.0.0", "binaries": [binary]},
                        "sibling": {"version": "1.0.0", "binaries": [binary]},
                    }
                )
            )
            with patch.object(
                refresh, "_release_digests", return_value={"tool.tar.gz": "sha256:new"}
            ):
                refresh.refresh_lockfile(path)
            result = json.loads(path.read_text())
            self.assertEqual(result["sibling"]["version"], result["tool"]["version"])
            self.assertEqual(result["sibling"]["binaries"][0]["sha256"], "new")

    def test_missing_digest_fails_without_rewriting_lockfile(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tool.lock.json"
            content = json.dumps(
                {
                    "tool": {
                        "version": "2.0.0",
                        "binaries": [
                            {
                                "url": "https://github.com/example/tool/releases/download/v1.0.0/tool.tar.gz",
                                "sha256": "old",
                            }
                        ],
                    }
                }
            )
            path.write_text(content)
            with (
                patch.object(refresh, "_release_digests", return_value={}),
                self.assertRaisesRegex(ValueError, "no digest"),
            ):
                refresh.refresh_lockfile(path)
            self.assertEqual(path.read_text(), content)


if __name__ == "__main__":
    unittest.main()
