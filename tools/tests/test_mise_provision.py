# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Keep mise setup selection and direct command paths tied to the catalog."""

import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT))
spec = importlib.util.spec_from_file_location(
    "score_mise_provision", TOOLS_ROOT / "internal/mise/provision.py"
)
mise_provision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mise_provision)


class DirectProvisionTest(unittest.TestCase):
    def test_pypi_install_stops_when_the_selected_uv_is_not_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_mise = root / "mise"
            fake_mise.write_text("#!/bin/sh\nexit 0\n")
            fake_mise.chmod(0o755)
            requested = {
                "uv": {
                    "profile": "native",
                    "version": "0.13.6",
                    "backend": "uv",
                    "entrypoint": "uv",
                },
                "pre-commit": {
                    "profile": "python",
                    "version": "4.7.0",
                    "backend": "pypi:pre-commit",
                    "entrypoint": "pre-commit",
                },
            }
            calls = []

            def run(command, **_kwargs):
                calls.append(command)
                action = command[command.index("-E") + 2]
                if action == "install":
                    return subprocess.CompletedProcess(command, 0)
                return subprocess.CompletedProcess(
                    command, 0, stdout='{"uv": []}', stderr=""
                )

            with (
                patch.object(
                    mise_provision, "_requested_tools", return_value=requested
                ),
                patch.object(mise_provision.subprocess, "run", side_effect=run),
                self.assertRaisesRegex(SystemExit, "selected uv at 0.13.6"),
            ):
                mise_provision.provision(
                    "repository",
                    data_dir=root / "data",
                    bin_dir=root / "bin",
                    mise_binary=fake_mise,
                )

            self.assertFalse(
                any(
                    "install" in call and call[call.index("-E") + 1] == "python"
                    for call in calls
                )
            )

    def test_selected_tools_are_installed_at_owner_pins_and_linked_directly(self):
        for environment in ("s-core-local", "bazel-feature"):
            with (
                self.subTest(environment=environment),
                tempfile.TemporaryDirectory() as tmp,
            ):
                root = Path(tmp)
                data_dir = root / "data"
                bin_dir = root / "bin"
                fake_mise = root / "mise"
                fake_mise.write_text("#!/bin/sh\nexit 0\n")
                fake_mise.chmod(0o755)
                requested = mise_provision._requested_tools(
                    environment, mise_provision.OWNER_ROOT
                )
                records = {}
                calls = []
                python_install_environments = []

                def run(command, **kwargs):
                    calls.append(command)
                    profile = command[command.index("-E") + 1]
                    action = command[command.index("-E") + 2]
                    env = kwargs["env"]
                    if action == "install":
                        selected = {
                            item["backend"]
                            for item in requested.values()
                            if item["profile"] == profile
                        }
                        for backend in selected:
                            item = next(
                                value
                                for value in requested.values()
                                if value["profile"] == profile
                                and value["backend"] == backend
                            )
                            install = (
                                Path(env["MISE_DATA_DIR"])
                                / "installs"
                                / backend.replace(":", "-").replace("/", "-")
                                / item["version"]
                            )
                            install.mkdir(parents=True, exist_ok=True)
                            executable_root = install
                            if backend == "uv":
                                # mise reports this parent as install_path; the
                                # actual uv binary lives in a nested directory.
                                executable_root = (
                                    install / "uv-x86_64-unknown-linux-gnu"
                                )
                                executable_root.mkdir()
                            matching = [
                                value
                                for value in requested.values()
                                if value["profile"] == profile
                                and value["backend"] == backend
                            ]
                            for value in matching:
                                executable = executable_root / value["entrypoint"]
                                executable.write_text(
                                    "#!/bin/sh\nprintf '%s\\n' "
                                    + value["version"]
                                    + "\n"
                                )
                                executable.chmod(0o755)
                            records.setdefault(profile, {})[backend] = {
                                "version": item["version"],
                                "install_path": str(install),
                                "installed": True,
                                "active": True,
                            }
                        if any(backend.startswith("pypi:") for backend in selected):
                            python_install_environments.append(env.copy())
                        return subprocess.CompletedProcess(command, 0)
                    self.assertEqual(action, "ls")
                    payload = {
                        backend: [record]
                        for backend, record in records.get(profile, {}).items()
                    }
                    return subprocess.CompletedProcess(
                        command, 0, stdout=json.dumps(payload), stderr=""
                    )

                ambient_bin = root / "ambient-bin"
                ambient_bin.mkdir()
                with (
                    patch.dict(os.environ, {"PATH": str(ambient_bin)}),
                    patch.object(mise_provision.subprocess, "run", side_effect=run),
                ):
                    installed = mise_provision.provision(
                        environment,
                        owner_root=mise_provision.OWNER_ROOT,
                        data_dir=data_dir,
                        bin_dir=bin_dir,
                        mise_binary=fake_mise,
                    )

                self.assertEqual(set(installed), set(requested))
                for name, executable in installed.items():
                    link = bin_dir / name
                    self.assertTrue(link.is_symlink())
                    self.assertEqual(link.resolve(), executable.resolve())
                    result = subprocess.run(
                        [str(link)], text=True, capture_output=True, check=True
                    )
                    self.assertEqual(result.stdout.strip(), requested[name]["version"])
                self.assertTrue(
                    all(
                        "--locked" in call
                        for call in calls
                        if "install" in call and call[call.index("-E") + 1] != "python"
                    )
                )
                self.assertFalse(any("exec" in call for call in calls))

                if environment == "s-core-local":
                    self.assertIn("apm", installed)
                    self.assertIn("opencode", installed)
                    self.assertIn("codespell", installed)
                    self.assertTrue(Path(os.readlink(bin_dir / "apm")).is_file())
                    self.assertEqual(len(python_install_environments), 1)
                    pypi_environment = python_install_environments[0]
                    uv_path = shutil.which("uv", path=pypi_environment["PATH"])
                    self.assertIsNotNone(uv_path)
                    self.assertEqual(Path(uv_path).resolve(), installed["uv"].resolve())
                    self.assertEqual(pypi_environment["MISE_PYPI_UVX"], "true")
                else:
                    self.assertIn("starpls", installed)
                    self.assertNotIn("codespell", installed)


class CommandOwnershipTest(unittest.TestCase):
    def test_fresh_prefix_rejects_an_untracked_selected_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            executable = root / "tool"
            executable.write_text("managed target")
            bin_dir.mkdir()
            (bin_dir / "tool").symlink_to(executable)

            with self.assertRaisesRegex(SystemExit, "unmanaged or user-replaced"):
                mise_provision.reconcile_commands(
                    "image", {"tool": executable}, bin_dir
                )

            self.assertEqual((bin_dir / "tool").resolve(), executable.resolve())
            self.assertFalse((bin_dir / mise_provision.OWNERSHIP_FILE).exists())

    def test_fresh_prefix_preserves_unrelated_user_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            executable = root / "managed-tool"
            executable.write_text("managed")
            bin_dir.mkdir()
            (bin_dir / "user-command").write_text("user")

            mise_provision.reconcile_commands("image", {"tool": executable}, bin_dir)

            self.assertEqual((bin_dir / "user-command").read_text(), "user")
            self.assertEqual((bin_dir / "tool").resolve(), executable.resolve())

    def test_reprovisioning_one_environment_preserves_shared_owner_until_last_removal(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            first = root / "first"
            second = root / "second"
            first.write_text("first")
            second.write_text("second")

            mise_provision.reconcile_commands("image-a", {"shared": first}, bin_dir)
            mise_provision.reconcile_commands("image-b", {"shared": first}, bin_dir)
            mise_provision.reconcile_commands("image-a", {}, bin_dir)

            self.assertTrue((bin_dir / "shared").is_symlink())
            self.assertEqual((bin_dir / "shared").resolve(), first.resolve())
            state = json.loads((bin_dir / mise_provision.OWNERSHIP_FILE).read_text())
            self.assertEqual(state["environments"], {"image-b": {"shared": str(first)}})

            mise_provision.reconcile_commands("image-b", {"second": second}, bin_dir)
            self.assertFalse((bin_dir / "shared").exists())
            self.assertEqual((bin_dir / "second").resolve(), second.resolve())

    def test_deselection_preserves_user_replaced_command_and_drops_stale_ownership(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            executable = root / "managed-tool"
            executable.write_text("managed")
            mise_provision.reconcile_commands("image", {"tool": executable}, bin_dir)

            replacement = bin_dir / "tool"
            replacement.unlink()
            replacement.write_text("user replacement")
            with patch("sys.stderr", new_callable=io.StringIO) as stderr:
                mise_provision.reconcile_commands("image", {}, bin_dir)

            self.assertEqual(replacement.read_text(), "user replacement")
            self.assertIn("Preserving user-replaced command", stderr.getvalue())
            self.assertFalse((bin_dir / mise_provision.OWNERSHIP_FILE).exists())

    def test_selection_refuses_foreign_command_without_removing_previous_owned_links(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            executable = root / "managed-tool"
            executable.write_text("managed")
            foreign = bin_dir / "foreign-tool"
            mise_provision.reconcile_commands("image", {"tool": executable}, bin_dir)
            foreign.parent.mkdir(parents=True, exist_ok=True)
            foreign.write_text("foreign")

            with self.assertRaisesRegex(SystemExit, "Refusing to replace unmanaged"):
                mise_provision.reconcile_commands(
                    "image", {"foreign-tool": executable}, bin_dir
                )

            self.assertEqual((bin_dir / "tool").resolve(), executable.resolve())
            self.assertEqual(foreign.read_text(), "foreign")

    def test_different_mise_targets_for_shared_command_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            first = root / "first"
            second = root / "second"
            first.write_text("first")
            second.write_text("second")
            mise_provision.reconcile_commands("image-a", {"tool": first}, bin_dir)

            with self.assertRaisesRegex(SystemExit, "already owned by image-a"):
                mise_provision.reconcile_commands("image-b", {"tool": second}, bin_dir)

            self.assertEqual((bin_dir / "tool").resolve(), first.resolve())


if __name__ == "__main__":
    unittest.main()
