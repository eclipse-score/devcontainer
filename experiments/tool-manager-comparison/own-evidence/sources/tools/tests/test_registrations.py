# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Removal changes fresh public outputs, not existing developer installations."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class RegistrationTest(unittest.TestCase):
    def test_removed_native_tool_is_not_offered_in_generated_bazel_or_inventory(self):
        source = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("tools", ".github", ".devcontainer", "src"):
                shutil.copytree(
                    source / name,
                    root / name,
                    ignore=shutil.ignore_patterns("__pycache__"),
                )
            for name in ("MODULE.bazel", ".bazelversion"):
                shutil.copyfile(source / name, root / name)
            (root / "tools/lockfiles/shellcheck.lock.json").unlink()
            selections = root / "tools/environments.json"
            data = json.loads(selections.read_text())
            for providers in data.values():
                providers["native"] = [
                    name for name in providers["native"] if name != "shellcheck"
                ]
            selections.write_text(json.dumps(data))
            script = root / "tools/internal/sync_readme.py"
            stale = subprocess.run(
                [sys.executable, script, "--check"], capture_output=True, text=True
            )
            self.assertEqual(stale.returncode, 1)
            self.assertIn("registrations are stale", stale.stderr)
            subprocess.run([sys.executable, script], check=True)
            subprocess.run([sys.executable, script, "--check"], check=True)
            self.assertNotIn(
                "shellcheck.lock.json", (root / "MODULE.bazel").read_text()
            )
            self.assertNotIn(
                'multitool_aliases("shellcheck")',
                (root / "tools/BUILD.bazel").read_text(),
            )
            self.assertNotIn("| `shellcheck`", (root / "tools/README.md").read_text())


if __name__ == "__main__":
    unittest.main()
