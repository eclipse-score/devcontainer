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
"""Regression checks for the generated Aqua bootstrap checksum manifest."""

from pathlib import Path
import sys
import tempfile
import tomllib
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "internal/aqua"))
from refresh_owners import BOOTSTRAP_PLATFORMS, refresh_bootstrap_checksums


class BootstrapChecksumRefreshTest(unittest.TestCase):
    def test_repeated_refresh_preserves_unrelated_archive_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            owner_dir = Path(directory)
            source = [
                'version = "2.65.2"',
                "",
            ]
            checksum_rows = []
            expected = {}
            for index, platform in enumerate(BOOTSTRAP_PLATFORMS, start=1):
                os_name, architecture = platform.split("/")
                name = f"aqua_{os_name}_{architecture}.tar.gz"
                digest = f"{index:064x}"
                expected[platform] = digest
                source.extend(
                    [
                        f'[archives."{platform}"]',
                        f'name = "{name}"',
                        'sha256 = "old"',
                        "",
                    ]
                )
                checksum_rows.append(f"{digest}  {name}")

            unrelated = (
                '[archives."windows/amd64"]\n'
                'name = "aqua_windows_amd64.zip"\n'
                'sha256 = "keep-this-digest"\n'
            )
            source.extend(
                [
                    '[archives."windows/amd64"]',
                    'name = "aqua_windows_amd64.zip"',
                    'sha256 = "keep-this-digest"',
                    "",
                ]
            )
            path = owner_dir / "aqua-bootstrap.toml"
            path.write_text("\n".join(source), encoding="utf-8")

            refresh_bootstrap_checksums(
                owner_dir, checksum_text="\n".join(checksum_rows)
            )
            first_refresh = path.read_text(encoding="utf-8")
            refresh_bootstrap_checksums(
                owner_dir, checksum_text="\n".join(checksum_rows)
            )
            second_refresh = path.read_text(encoding="utf-8")

            self.assertEqual(second_refresh, first_refresh)
            self.assertIn(unrelated, first_refresh)
            manifest = tomllib.loads(second_refresh)
            for platform, digest in expected.items():
                self.assertEqual(manifest["archives"][platform]["sha256"], digest)
            self.assertEqual(
                manifest["archives"]["windows/amd64"]["sha256"],
                "keep-this-digest",
            )


if __name__ == "__main__":
    unittest.main()
