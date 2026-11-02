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
"""Regression checks for safe reconciliation of reused host tool prefixes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "internal/devcontainer"))
import provision_host_tools


class HostToolReconciliationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.prefix = Path(self.temporary.name)
        self.bin = self.prefix / "bin"
        self.bin.mkdir()

    def _command(self, name: str, content: str) -> dict:
        path = self.bin / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)
        return provision_host_tools._command_identity(path)

    def _fake_aqua_cp(self, *, omit: set[str] | None = None):
        omitted = omit or set()

        def fake_run(args, check, env):
            output = Path(args[args.index("-o") + 1])
            requested = args[args.index("-o") + 2 :]
            for name in (*requested, "gh"):
                if name in omitted:
                    continue
                executable = output / name
                executable.write_text(
                    f"#!/bin/sh\nprintf '%s\\n' '{name}'\n", encoding="utf-8"
                )
                executable.chmod(0o755)
            return None

        return fake_run

    def _copy_aqua_commands(self, commands: list[str]) -> None:
        with patch.object(
            provision_host_tools.subprocess,
            "run",
            side_effect=self._fake_aqua_cp(),
        ) as run:
            provision_host_tools._copy_selected_aqua_commands(
                "aqua",
                Path("aqua.yaml"),
                "repository",
                sorted(commands),
                self.prefix,
                self.bin,
                {},
            )
        invocation = run.call_args.args[0]
        requested = invocation[invocation.index("-o") + 2 :]
        self.assertNotIn("gh", requested)

    def test_removes_deselected_owned_command_but_keeps_other_profile_owner(self):
        """A shared selection retains its path when another profile still owns it."""
        shared = self._command("shared", "#!/bin/sh\nexit 0\n")
        retired = self._command("retired", "#!/bin/sh\nexit 0\n")
        self._command("foreign", "#!/bin/sh\nexit 0\n")
        state = {
            "schema_version": 1,
            "profiles": {
                "repository": {
                    "owner_digest": "old-repository",
                    "commands": {"shared": shared, "retired": retired},
                },
                "published": {
                    "owner_digest": "old-published",
                    "commands": {"shared": shared},
                },
            },
        }

        removed = provision_host_tools._reconcile_commands(
            self.prefix,
            state,
            {"repository": ["shared"], "published": ["shared"]},
            "repository",
            "new-repository",
            ["shared"],
        )

        self.assertEqual(removed, ["retired"])
        self.assertTrue((self.bin / "shared").is_file())
        self.assertTrue((self.bin / "foreign").is_file())
        self.assertFalse((self.bin / "retired").exists())
        self.assertEqual(set(state["profiles"]), {"repository", "published"})
        self.assertEqual(
            json.loads((self.prefix / ".score-tools-owner.json").read_text()), state
        )

    def test_preserves_user_replaced_command_when_its_last_profile_deselects_it(self):
        """A changed path stops being owned and remains available to its user."""
        original = self._command("retired", "#!/bin/sh\necho manager\n")
        (self.bin / "retired").write_text("#!/bin/sh\necho user\n", encoding="utf-8")
        (self.bin / "retired").chmod(0o755)
        state = {
            "schema_version": 1,
            "profiles": {
                "repository": {
                    "owner_digest": "old",
                    "commands": {"retired": original},
                }
            },
        }

        removed = provision_host_tools._reconcile_commands(
            self.prefix, state, {"repository": []}, "repository", "new", []
        )

        self.assertEqual(removed, [])
        self.assertIn("user", (self.bin / "retired").read_text())
        self.assertEqual(state["profiles"]["repository"]["commands"], {})

    def test_refuses_to_overwrite_user_replacement_of_still_selected_command(self):
        """A selected path with a changed fingerprint requires manual resolution."""
        original = self._command("selected", "#!/bin/sh\necho manager\n")
        (self.bin / "selected").write_text("#!/bin/sh\necho user\n", encoding="utf-8")
        (self.bin / "selected").chmod(0o755)
        state = {
            "schema_version": 1,
            "profiles": {
                "repository": {
                    "owner_digest": "old",
                    "commands": {"selected": original},
                }
            },
        }

        with self.assertRaisesRegex(SystemExit, "user-replaced"):
            provision_host_tools._validate_selected_paths(
                self.prefix, ["selected"], state
            )

    def test_refuses_to_overwrite_foreign_command_in_selected_path(self):
        """An untracked executable is not claimed just because its name is selected."""
        self._command("foreign-tool", "#!/bin/sh\necho user\n")

        with self.assertRaisesRegex(SystemExit, "unmanaged"):
            provision_host_tools._validate_selected_paths(
                self.prefix,
                ["foreign-tool"],
                {"schema_version": 1, "profiles": {}},
            )

    def test_preserves_a_command_whose_symlink_target_was_user_modified(self):
        """Symlink identity includes its target bytes before a stale link is removed."""
        target = self.prefix / "tool-body"
        target.write_text("#!/bin/sh\necho manager\n", encoding="utf-8")
        target.chmod(0o755)
        command = self.bin / "command"
        command.symlink_to(target)
        original = provision_host_tools._command_identity(command)
        target.write_text("#!/bin/sh\necho user\n", encoding="utf-8")
        state = {
            "schema_version": 1,
            "profiles": {
                "repository": {
                    "owner_digest": "old",
                    "commands": {"command": original},
                }
            },
        }

        removed = provision_host_tools._reconcile_commands(
            self.prefix, state, {"repository": []}, "repository", "new", []
        )

        self.assertEqual(removed, [])
        self.assertTrue(command.is_symlink())
        self.assertIn("user", target.read_text())

    def test_requires_a_fresh_prefix_when_ownership_state_is_untracked(self):
        """Unknown prefixes need a new ledger because command identities are absent."""
        (self.prefix / ".score-tools-owner.json").write_text(
            '{"profile": "repository", "owner_digest": "old"}\n',
            encoding="utf-8",
        )

        with self.assertRaisesRegex(SystemExit, "fresh --prefix"):
            provision_host_tools._read_state(self.prefix)

    def test_python_command_identity_includes_every_console_script(self):
        """The provisioner tracks secondary uv-created command names as owned too."""
        definitions = provision_host_tools._python_catalog()

        self.assertEqual(
            provision_host_tools._expected_python_commands(
                ["pytest==9.0.2", "basedpyright==1.35.0"], definitions
            ),
            {
                "pytest",
                "py.test",
                "basedpyright",
                "basedpyright-langserver",
            },
        )

    def test_aqua_extra_command_stays_private_and_deselected_command_is_retired(self):
        """Aqua cp extras stay staged while selected commands reconcile normally."""
        first_selection = ["buildifier", "uv", "uvx"]
        self._copy_aqua_commands(first_selection)
        self.assertFalse((self.bin / "gh").exists())
        for command in first_selection:
            self.assertTrue((self.bin / command).is_file())
            self.assertTrue(os.access(self.bin / command, os.X_OK))

        state = {"schema_version": 1, "profiles": {}}
        provision_host_tools._reconcile_commands(
            self.prefix,
            state,
            {"repository": first_selection},
            "repository",
            "first-selection",
            first_selection,
        )

        next_selection = ["uv", "uvx"]
        self._copy_aqua_commands(next_selection)
        retired = provision_host_tools._reconcile_commands(
            self.prefix,
            state,
            {"repository": next_selection},
            "repository",
            "next-selection",
            next_selection,
        )

        self.assertEqual(retired, ["buildifier"])
        self.assertFalse((self.bin / "buildifier").exists())
        self.assertFalse((self.bin / "gh").exists())
        self.assertEqual(
            subprocess.check_output([str(self.bin / "uv")], text=True).strip(),
            "uv",
        )

    def test_aqua_extra_command_does_not_replace_foreign_prefix_command(self):
        """An unselected Aqua output cannot overwrite a foreign shared-bin path."""
        sentinel = self.bin / "gh"
        sentinel.write_text("foreign gh sentinel\n", encoding="utf-8")

        self._copy_aqua_commands(["uv"])

        self.assertEqual(sentinel.read_text(encoding="utf-8"), "foreign gh sentinel\n")
        self.assertTrue(os.access(self.bin / "uv", os.X_OK))

    def test_aqua_missing_selected_output_fails_before_exposure(self):
        """Every selected native command must be present in Aqua cp output."""
        with patch.object(
            provision_host_tools.subprocess,
            "run",
            side_effect=self._fake_aqua_cp(omit={"uv"}),
        ):
            with self.assertRaisesRegex(SystemExit, "selected executable commands"):
                provision_host_tools._copy_selected_aqua_commands(
                    "aqua",
                    Path("aqua.yaml"),
                    "repository",
                    ["uv"],
                    self.prefix,
                    self.bin,
                    {},
                )
        self.assertFalse((self.bin / "uv").exists())


if __name__ == "__main__":
    unittest.main()
