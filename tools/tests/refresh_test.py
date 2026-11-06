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
"""A version bump must refresh every artifact or leave the file untouched."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.internal import refresh_lockfile_digests as refresh

SHA256 = "a" * 64


class RefreshTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "example.lock.json"

    def prepare(self, prefix="v"):
        # Only the pin has changed; URLs and archive paths still name 1.0.0.
        binaries = [
            {
                "url": f"https://github.com/acme/example/releases/download/{prefix}1.0.0/example_1.0.0_{cpu}.tar.gz",
                "file": "example-1.0.0/example",
                "sha256": "0" * 64,
            }
            for cpu in ("amd64", "arm64")
        ]
        self.path.write_text(
            json.dumps({"example": {"version": "2.0.0", "binaries": binaries}})
        )
        return {
            "assets": [
                {"name": f"example_2.0.0_{cpu}.tar.gz", "digest": f"sha256:{SHA256}"}
                for cpu in ("amd64", "arm64")
            ]
        }

    def test_bump_updates_tag_asset_archive_path_and_checksum_for_each_platform(self):
        for prefix in ("v", ""):
            with self.subTest(tag_prefix=prefix):
                with patch.object(
                    refresh, "_api_get", return_value=self.prepare(prefix)
                ):
                    refresh.refresh_lockfile(self.path)
                binaries = json.loads(self.path.read_text())["example"]["binaries"]
                for binary, cpu in zip(binaries, ("amd64", "arm64")):
                    self.assertEqual(
                        binary["url"],
                        f"https://github.com/acme/example/releases/download/{prefix}2.0.0/example_2.0.0_{cpu}.tar.gz",
                    )
                    self.assertEqual(binary["file"], "example-2.0.0/example")
                    self.assertEqual(binary["sha256"], SHA256)

    def test_missing_asset_or_invalid_digest_preserves_the_entire_file(self):
        # Fail on the second platform after the first was processed successfully.
        for invalid in ("missing", None, "sha256:short"):
            with self.subTest(digest=invalid):
                release = self.prepare()
                original = self.path.read_bytes()
                if invalid == "missing":
                    release["assets"].pop()
                else:
                    release["assets"][-1]["digest"] = invalid
                with patch.object(refresh, "_api_get", return_value=release):
                    with self.assertRaises(ValueError):
                        refresh.refresh_lockfile(self.path)
                self.assertEqual(self.path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
