# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Safe additive provisioning and portable installer regressions."""

import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_tools import provision as p


class ProvisionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.packages = self.root / "data/packages"
        self.target = self.packages / "fixture/tool"
        self.target.parent.mkdir(parents=True)
        self.target.write_text("#!/bin/sh\nexit 0\n")
        self.target.chmod(0o755)
        self.other = self.target.with_name("other")
        self.other.write_text("#!/bin/sh\nexit 0\n")
        self.other.chmod(0o755)

    def test_repeat_update_and_empty_selection_preserve_unselected_and_user_files(self):
        p.publish({"tool": self.target}, self.bin, self.packages)
        p.publish({"tool": self.target}, self.bin, self.packages)
        (self.bin / "sentinel").write_text("user")
        p.publish({"tool": self.other}, self.bin, self.packages)
        p.publish({}, self.bin, self.packages)
        self.assertEqual((self.bin / "tool").resolve(), self.other)
        self.assertEqual((self.bin / "sentinel").read_text(), "user")
        self.assertTrue(self.target.exists())

    def test_untracked_files_directories_and_foreign_links_are_not_adopted(self):
        path = self.bin / "tool"
        for kind in ("file", "directory", "foreign", "dangling"):
            if kind == "file":
                path.write_text("user")
            elif kind == "directory":
                path.mkdir()
            else:
                path.symlink_to(
                    self.root / ("foreign" if kind == "foreign" else "missing")
                )
            with self.assertRaisesRegex(ValueError, "unmanaged"):
                p.publish({"tool": self.target}, self.bin, self.packages)
            path.rmdir() if kind == "directory" else path.unlink()

    def test_user_replaced_command_is_not_overwritten(self):
        p.publish({"tool": self.target}, self.bin, self.packages)
        (self.bin / "tool").unlink()
        (self.bin / "tool").write_text("user")
        with self.assertRaisesRegex(ValueError, "user-replaced"):
            p.publish({"tool": self.other}, self.bin, self.packages)
        self.assertEqual((self.bin / "tool").read_text(), "user")

    def test_all_conflicts_checked_before_changing_any_link(self):
        p.publish({"tool": self.target}, self.bin, self.packages)
        (self.bin / "other").write_text("user")
        with self.assertRaisesRegex(ValueError, "unmanaged"):
            p.publish(
                {"tool": self.other, "other": self.other}, self.bin, self.packages
            )
        self.assertEqual((self.bin / "tool").resolve(), self.target)

    def test_strict_call_preserves_cwd_argv_and_status(self):
        self.target.write_text('#!/bin/sh\nprintf \'%s\\n\' "$PWD" "$@"\nexit 37\n')
        p.publish({"tool": self.target}, self.bin, self.packages)
        result = subprocess.run(
            [
                "/bin/bash",
                str(p.TOOLS_ROOT / "run-tool"),
                "--strict",
                "tool",
                "spaced file",
                "--flag",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            env={
                **os.environ,
                "RUN_TOOL_CONTAINER_MODE": "host",
                "SCORE_TOOLS_PREFIX": str(self.root),
                "PATH": "/usr/bin:/bin",
            },
        )
        self.assertEqual(result.returncode, 37)
        self.assertEqual(
            result.stdout.splitlines(), [str(self.root), "spaced file", "--flag"]
        )

    def test_invalid_selection_fails_before_downloads(self):
        with patch.object(p, "install_native") as install, self.assertRaises(KeyError):
            p.provision(
                "fixture",
                ["uv", "unknown"],
                [],
                bin_dir=self.bin,
                data_dir=self.root / "data",
            )
        install.assert_not_called()

    def test_duplicate_selected_command_fails_before_preparing_payloads(self):
        with (
            patch.object(
                p,
                "_load_python_tools",
                return_value={
                    "fixture": {
                        "entrypoint": "uv",
                        "package": "fixture",
                        "version": "1.0",
                        "description": "fixture",
                    }
                },
            ),
            patch.object(p, "prepare_native") as prepare,
            self.assertRaisesRegex(ValueError, "Duplicate selected command"),
        ):
            p.provision(
                "fixture",
                ["uv"],
                ["fixture"],
                bin_dir=self.bin,
                data_dir=self.root / "data",
            )
        prepare.assert_not_called()

    def test_python_uses_provisioning_interpreter_unless_explicitly_selected(self):
        with patch.object(p.subprocess, "run") as run:
            p.install_python(
                ["fixture==1.0"],
                "/fixture/uv",
                bin_dir=self.bin,
                tool_dir=self.root / "tools",
            )
        self.assertEqual(
            run.call_args.kwargs["env"]["UV_PYTHON"],
            os.environ.get("UV_PYTHON", sys.executable),
        )
        with (
            patch.dict(os.environ, {"UV_PYTHON": "/selected/python"}),
            patch.object(p.subprocess, "run") as run,
        ):
            p.install_python(
                ["fixture==1.0"],
                "/fixture/uv",
                bin_dir=self.bin,
                tool_dir=self.root / "tools",
            )
        self.assertEqual(run.call_args.kwargs["env"]["UV_PYTHON"], "/selected/python")

    def data(self, path, **fields):
        return {
            "version": "1.0",
            "binaries": [
                {
                    "os": "linux",
                    "cpu": "x86_64",
                    "kind": "file",
                    "url": path.as_uri(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    **fields,
                }
            ],
        }

    def test_file_download_checksum_and_prepared_reuse_without_network(self):
        source = self.root / "source"
        source.write_text("#!/bin/sh\nexit 0\n")
        data = self.data(source)
        target = p.install_native("tool", data, self.packages, ("linux", "x86_64"))
        with patch.object(
            p.urllib.request, "urlopen", side_effect=AssertionError("network")
        ):
            self.assertEqual(
                p.install_native("tool", data, self.packages, ("linux", "x86_64")),
                target,
            )
        self.assertTrue(os.access(target, os.X_OK))

    def test_bad_checksum_does_not_publish_a_package(self):
        source = self.root / "source"
        source.write_text("payload")
        data = self.data(source)
        data["binaries"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            p.install_native("tool", data, self.packages, ("linux", "x86_64"))
        self.assertFalse(
            any(path.name.startswith("artifact-") for path in self.packages.iterdir())
        )

    def test_tar_member_and_whole_runtime_directory(self):
        archive = self.root / "archive.tar.gz"
        with tarfile.open(archive, "w:gz") as output:
            for name, content in (
                ("runtime/tool", b"executable"),
                ("runtime/_internal/data", b"runtime"),
            ):
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(content), 0o755
                output.addfile(info, io.BytesIO(content))
        for fields in ({"file": "runtime/tool"}, {"dir": "runtime"}):
            with tempfile.TemporaryDirectory(dir=self.root) as destination:
                p.unpack(
                    {"kind": "archive", "type": "tar.gz", **fields},
                    archive,
                    Path(destination),
                    "tool",
                )
                self.assertEqual(
                    (Path(destination) / "tool").read_bytes(), b"executable"
                )
                if "dir" in fields:
                    self.assertEqual(
                        (Path(destination) / "_internal/data").read_bytes(), b"runtime"
                    )

    def test_zip_single_member(self):
        archive = self.root / "archive.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("nested/tool", "executable")
        p.unpack(
            {"kind": "archive", "type": "zip", "file": "nested/tool"},
            archive,
            self.root,
            "tool",
        )
        self.assertEqual((self.root / "tool").read_text(), "executable")

    def test_shared_archive_siblings_are_adjacent_and_downloaded_once(self):
        archive = self.root / "archive.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("tool", "executable")
            output.writestr("sibling", "adjacent dependency")
        data = self.data(archive, kind="archive", type="zip", file="tool")
        sibling = self.data(archive, kind="archive", type="zip", file="sibling")
        definitions = {"tool": data, "sibling": sibling}
        target = p.prepare_native(
            "sibling", definitions, self.packages, ("linux", "x86_64")
        )
        self.assertEqual((target.parent / "tool").read_text(), "executable")
        with patch.object(
            p.urllib.request, "urlopen", side_effect=AssertionError("network")
        ):
            other = p.prepare_native(
                "tool", definitions, self.packages, ("linux", "x86_64")
            )
        self.assertEqual(other.parent, target.parent)

    def test_transient_download_failure_is_bounded_and_reported(self):
        with (
            patch.object(
                p.urllib.request, "urlopen", side_effect=TimeoutError("fixture timeout")
            ) as request,
            patch.object(p.time, "sleep"),
            patch.object(p.sys, "stderr", new_callable=io.StringIO) as errors,
            self.assertRaises(TimeoutError),
        ):
            p.download("https://example.invalid/artifact", self.root / "download")
        self.assertEqual(request.call_count, 3)
        self.assertIn("attempt 1/3 failed", errors.getvalue())
        self.assertIn("attempt 2/3 failed", errors.getvalue())

    def test_traversal_and_symlinks_rejected_before_directory_extraction(self):
        for malicious in ("runtime/../../escape", "runtime/link"):
            archive = self.root / "bad.tar"
            with tarfile.open(archive, "w") as output:
                info = tarfile.TarInfo(malicious)
                if malicious.endswith("link"):
                    info.type, info.linkname = tarfile.SYMTYPE, "/tmp"
                output.addfile(info)
            with self.assertRaisesRegex(
                ValueError, "Unsafe archive|Unsupported archive"
            ):
                p.unpack(
                    {"kind": "archive", "dir": "runtime"}, archive, self.root, "tool"
                )


if __name__ == "__main__":
    unittest.main()
