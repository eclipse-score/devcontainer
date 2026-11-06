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
"""Version bumps must produce complete, installable native tool lockfiles."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.internal import refresh_lockfile_digests as refresh

LOCKFILES = Path(__file__).resolve().parents[1] / "lockfiles"
SHA256 = "a" * 64


class RefreshTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "tool.lock.json"

    def prepare(self, name, version):
        data = json.loads((LOCKFILES / f"{name}.lock.json").read_text())
        for tool in data.values():
            if isinstance(tool, dict) and "binaries" in tool:
                tool["version"] = version
        self.path.write_text(json.dumps(data))
        return data

    def test_versioned_assets_and_archive_members_follow_the_pin(self):
        data = self.prepare("shellcheck", "0.11.0")
        assets = [
            {
                "name": binary["url"].rsplit("/", 1)[1].replace("0.10.0", "0.11.0"),
                "digest": f"sha256:{SHA256}",
            }
            for binary in data["shellcheck"]["binaries"]
        ]
        with patch.object(refresh, "_api_get", return_value={"assets": assets}) as api:
            refresh.refresh_lockfile(self.path)
            api.assert_called_once_with(
                "https://api.github.com/repos/koalaman/shellcheck/releases/tags/v0.11.0",
                None,
            )
            updated = json.loads(self.path.read_text())
            for binary in updated["shellcheck"]["binaries"]:
                self.assertIn("/v0.11.0/shellcheck-v0.11.0.", binary["url"])
                self.assertEqual(binary["file"], "shellcheck-v0.11.0/shellcheck")
                self.assertEqual(binary["sha256"], SHA256)
            self.assertEqual(refresh.refresh_lockfile(self.path), [])

    def test_shared_release_with_bare_tag_updates_both_uv_commands(self):
        data = self.prepare("uv", "0.14.0")
        assets = [
            {"name": binary["url"].rsplit("/", 1)[1], "digest": f"sha256:{SHA256}"}
            for binary in data["uv"]["binaries"]
        ]
        with patch.object(refresh, "_api_get", return_value={"assets": assets}) as api:
            refresh.refresh_lockfile(self.path)
        api.assert_called_once_with(
            "https://api.github.com/repos/astral-sh/uv/releases/tags/0.14.0", None
        )
        updated = json.loads(self.path.read_text())
        for name in ("uv", "uvx"):
            for before, after in zip(data[name]["binaries"], updated[name]["binaries"]):
                self.assertEqual(
                    after["url"], before["url"].replace("0.13.7", "0.14.0")
                )
                self.assertEqual(after["file"], before["file"])
                self.assertEqual(after["sha256"], SHA256)

    def test_incomplete_release_fails_without_writing_any_platform(self):
        # The last platform fails after earlier ones were processed successfully.
        # A failed refresh must preserve the entire input, not partly update it.
        for invalid in ("missing", None, "sha256:short", "sha512:" + "a" * 128):
            with self.subTest(digest=invalid):
                data = self.prepare("uv", "0.14.0")
                original = self.path.read_bytes()
                assets = [
                    {
                        "name": binary["url"].rsplit("/", 1)[1],
                        "digest": f"sha256:{SHA256}",
                    }
                    for binary in data["uv"]["binaries"]
                ]
                if invalid == "missing":
                    assets.pop()
                else:
                    assets[-1]["digest"] = invalid
                with patch.object(refresh, "_api_get", return_value={"assets": assets}):
                    with self.assertRaisesRegex(ValueError, "missing asset|SHA256"):
                        refresh.refresh_lockfile(self.path)
                self.assertEqual(self.path.read_bytes(), original)

    def test_unsupported_release_url_is_an_error(self):
        data = self.prepare("uv", "0.14.0")
        data["uv"]["binaries"][0]["url"] = "https://example.org/uv.tar.gz"
        self.path.write_text(json.dumps(data))
        with patch.object(refresh, "_api_get", return_value={"assets": []}):
            with self.assertRaisesRegex(ValueError, "unsupported release URL"):
                refresh.refresh_lockfile(self.path)


if __name__ == "__main__":
    unittest.main()
