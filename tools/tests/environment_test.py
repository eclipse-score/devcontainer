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
"""Check selected tools are installed and invalid selections fail before installation."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.internal import catalog
from tools.internal.devcontainer import install as installer

TOOLS_DIR = Path(__file__).resolve().parents[1]


class EnvironmentTest(unittest.TestCase):
    def test_rejects_invalid_selection_data_and_wrong_providers(self) -> None:
        cases = (
            ([], "must be a dictionary"),
            ({"": {"native": []}}, "names must be nonempty"),
            ({"ci": []}, "Invalid provider categories"),
            ({"ci": {"unknown": []}}, "Invalid provider categories"),
            ({"ci": {"native": "ruff"}}, "must be a tool list"),
            ({"ci": {"native": [7]}}, "must be a tool list"),
            ({"ci": {"native": ["ruff", "ruff"]}}, "more than once"),
            ({"ci": {"native": ["missing"]}}, "Unknown tool 'missing'"),
            ({"ci": {"native": ["pre-commit"]}}, "Wrong provider for 'pre-commit'"),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "environments.json"
            with patch.object(catalog, "ENVIRONMENTS_PATH", path):
                for data, message in cases:
                    with self.subTest(data=data):
                        path.write_text(json.dumps(data), encoding="utf-8")
                        with self.assertRaisesRegex(SystemExit, message):
                            catalog.load_environments()

    def test_copied_installer_applies_an_independent_ci_selection(self) -> None:
        # A new image can declare its own tool list without changing the
        # installer. Local files exercise the real download/checksum/install path.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = self._copy_tools(root)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            metadata = {}
            for name in ("lint", "check"):
                source = artifacts / name
                source.write_text(f"#!/bin/sh\nprintf '%s\\n' '{name} 1.0'\n")
                metadata[name] = {
                    "version": "1.0",
                    "binaries": [
                        {
                            "os": "linux",
                            "cpu": "arm64",
                            "kind": "file",
                            "url": source.as_uri(),
                            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        }
                    ],
                }
            (tools / "lockfiles/ci.lock.json").write_text(json.dumps(metadata))
            (tools / "environments.json").write_text(
                json.dumps(
                    {
                        "ci": {"native": ["lint", "check"]},
                        "unused": {"native": ["ruff"]},
                    }
                )
            )
            destination = root / "ci tools"
            result = self._run(tools, root, "ci", destination)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual({p.name for p in destination.iterdir()}, {"lint", "check"})
            for name in ("lint", "check"):
                self.assertEqual(
                    (destination / name).read_bytes(), (artifacts / name).read_bytes()
                )
                self.assertTrue((destination / name).stat().st_mode & 0o111)

    def test_invalid_later_tool_or_platform_prevents_any_download(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = self._copy_tools(root)
            # The first URL deliberately does not exist. If installation starts
            # before validating the second entry, this produces the wrong error.
            first = {
                "version": "1.0",
                "binaries": [
                    {
                        "os": "linux",
                        "cpu": "arm64",
                        "kind": "file",
                        "url": (root / "must-not-be-downloaded").as_uri(),
                        "sha256": "0" * 64,
                    }
                ],
            }
            unsupported = {"version": "1.0", "binaries": []}
            (tools / "lockfiles/fixture.lock.json").write_text(
                json.dumps(
                    {
                        "first": first,
                        "unsupported": unsupported,
                    }
                )
            )
            for second, message in (
                ("missing", "Unknown tool 'missing'"),
                ("unsupported", "Tool 'unsupported': No binary defined"),
            ):
                with self.subTest(second=second):
                    (tools / "environments.json").write_text(
                        json.dumps(
                            {
                                "ci": {"native": ["first", second]},
                            }
                        )
                    )
                    destination = root / "not-created"
                    result = self._run(tools, root, "ci", destination)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)
                    self.assertFalse(destination.exists())

    def test_unknown_environment_is_reported_without_installing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = self._copy_tools(root)
            destination = root / "not-created"
            result = self._run(tools, root, "no-such-environment", destination)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "Unknown tool environment 'no-such-environment'", result.stderr
            )
            self.assertFalse(destination.exists())

    def test_complete_selection_preserves_provider_order_and_package_policies(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = self._copy_tools(root)
            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            # Fake apt/npm/uv commands record what would be installed without
            # changing host packages. uv itself comes from a checksum-checked file.
            recorder = (
                f"#!{sys.executable}\n"
                "import json, os, sys\n"
                "from pathlib import Path\n"
                "with open(os.environ['SCORE_TEST_LOG'], 'a') as log:\n"
                "    log.write(json.dumps({'command': Path(sys.argv[0]).name, "
                "'args': sys.argv[1:], 'bin_dir': os.environ.get('UV_TOOL_BIN_DIR'), "
                "'tool_dir': os.environ.get('UV_TOOL_DIR'), "
                "'privileged': os.environ.get('SCORE_TEST_PRIVILEGED')}) + '\\n')\n"
            )
            for name in ("apt-get", "npm"):
                executable = fake_bin / name
                executable.write_text(recorder)
                executable.chmod(0o755)
            uv_artifact = root / "uv-artifact"
            uv_artifact.write_text(recorder)
            (tools / "lockfiles/uv.lock.json").write_text(
                json.dumps(
                    {
                        "uv": {
                            "version": "test",
                            "binaries": [
                                {
                                    "os": "linux",
                                    "cpu": "arm64",
                                    "kind": "file",
                                    "url": uv_artifact.as_uri(),
                                    "sha256": hashlib.sha256(
                                        uv_artifact.read_bytes()
                                    ).hexdigest(),
                                }
                            ],
                        },
                    }
                )
            )
            providers = {
                "regular": {
                    "provider": "apt",
                    "packages": ["regular"],
                    "policy": "prefix",
                    "version": "1:2.3",
                    "platforms": ["linux/arm64"],
                },
                "minimal": {
                    "provider": "apt",
                    "packages": ["minimal"],
                    "policy": "distribution",
                    "install_recommends": False,
                    "platforms": ["linux/arm64"],
                },
                "build-helper": {
                    "provider": "apt",
                    "packages": ["build-helper"],
                    "policy": "distribution",
                    "phase": "build-only",
                    "platforms": ["linux/arm64"],
                },
                "cli": {"provider": "npm", "package": "@fixture/cli"},
            }
            providers["pre-commit"] = catalog.load_providers()["pre-commit"]
            (tools / "providers.json").write_text(json.dumps(providers))
            selection = {
                "native": ["uv"],
                "python": ["pre-commit"],
                "apt": ["regular", "minimal"],
                "build-apt": ["build-helper"],
                "npm": ["cli"],
            }
            (tools / "environments.json").write_text(json.dumps({"ci": selection}))
            destination = root / "bin"
            tool_dir = root / "python tools"
            log = root / "calls.jsonl"
            environment = dict(
                os.environ,
                PATH=str(fake_bin) + os.pathsep + os.environ["PATH"],
                SCORE_TEST_LOG=str(log),
            )
            # One ordinary invocation installs build dependencies, applies tools,
            # and removes the temporary dependencies after successful setup.
            result = self._run(
                tools,
                root,
                "ci",
                destination,
                "--tool-dir",
                str(tool_dir),
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(
                [(c["command"], c["args"]) for c in calls],
                [
                    ("apt-get", ["install", "-y", "build-helper"]),
                    ("apt-get", ["install", "-y", "regular=1:2.3*"]),
                    (
                        "apt-get",
                        [
                            "install",
                            "-y",
                            "--no-install-recommends",
                            "--fix-broken",
                            "minimal",
                        ],
                    ),
                    ("uv", ["tool", "install", "--force", "pre-commit==4.7.0"]),
                    ("npm", ["install", "-g", "@fixture/cli"]),
                    ("apt-get", ["remove", "--purge", "-y", "build-helper"]),
                ],
            )
            self.assertEqual(calls[3]["bin_dir"], str(destination))
            self.assertEqual(calls[3]["tool_dir"], str(tool_dir))
            # The installer elevates system tools but keeps npm in the user's
            # environment. This fixture's sudo records that boundary without root.
            expected_privilege = "1" if os.geteuid() != 0 else None
            self.assertTrue(
                all(
                    c["privileged"] == expected_privilege
                    for c in calls
                    if c["command"] != "npm"
                )
            )
            self.assertIsNone(calls[4]["privileged"])
            # A provider filter still permits installing just one group.
            log.unlink()
            result = self._run(
                tools, root, "ci", destination, "--providers", "npm", env=environment
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            npm_only = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(
                [(c["command"], c["args"]) for c in npm_only],
                [("npm", ["install", "-g", "@fixture/cli"])],
            )
            # Removing a group from the selection must stop its install commands,
            # not just change the displayed tool list.
            (tools / "environments.json").write_text(
                json.dumps({"ci": {"apt": ["minimal"]}})
            )
            log.unlink()
            result = self._run(tools, root, "ci", destination, env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            remaining = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([c["command"] for c in remaining], ["apt-get"])
            self.assertEqual(remaining[0]["args"][-1], "minimal")

    def test_repository_setup_elevates_system_tools_and_keeps_npm_in_caller(
        self,
    ) -> None:
        with (
            patch.object(installer.os, "geteuid", return_value=1000),
            patch.object(installer, "_is_writable", return_value=False),
            patch.object(installer, "_cmd_install") as native,
            patch.object(installer, "_cmd_install_python") as python,
            patch.object(installer.subprocess, "run") as run,
        ):
            result = installer.main(
                [
                    "install-environment",
                    "repository-devcontainer",
                    "--os",
                    "linux",
                    "--cpu",
                    "arm64",
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(run.call_count, 2)
        system, npm = [call.args[0] for call in run.call_args_list]
        self.assertEqual(system[:2], ["sudo", sys.executable])
        self.assertEqual(
            system[system.index("--providers") + 1 :], ["native", "python"]
        )
        self.assertIn("/usr/local/bin", system)
        self.assertIn("/usr/local/share/uv/tools", system)
        self.assertEqual(npm, ["npm", "install", "-g", "@devcontainers/cli"])
        native.assert_not_called()
        python.assert_not_called()

    def test_root_image_build_does_not_delegate_or_repeat_installation(self) -> None:
        with (
            patch.object(installer.os, "geteuid", return_value=0),
            patch.object(installer, "_cmd_install") as native,
            patch.object(installer, "_cmd_install_python") as python,
            patch.object(installer.subprocess, "run") as run,
        ):
            result = installer.main(
                [
                    "install-environment",
                    "repository-devcontainer",
                    "--os",
                    "linux",
                    "--cpu",
                    "arm64",
                ]
            )
        self.assertEqual(result, 0)
        native.assert_called_once()
        python.assert_called_once()
        run.assert_called_once_with(
            ["npm", "install", "-g", "@devcontainers/cli"], check=True
        )

    def test_failed_system_installation_stops_before_npm(self) -> None:
        with (
            patch.object(installer.os, "geteuid", return_value=1000),
            patch.object(installer, "_is_writable", return_value=False),
            patch.object(
                installer.subprocess,
                "run",
                side_effect=subprocess.CalledProcessError(1, "sudo"),
            ) as run,
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                installer.main(
                    [
                        "install-environment",
                        "repository-devcontainer",
                        "--os",
                        "linux",
                        "--cpu",
                        "arm64",
                    ]
                )
        run.assert_called_once()

    def test_writable_native_destination_does_not_require_sudo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = installer._build_parser().parse_args(
                [
                    "install-environment",
                    "fixture",
                    "--destination",
                    str(Path(directory) / "new" / "bin"),
                ]
            )
            with (
                patch.object(installer.os, "geteuid", return_value=1000),
                patch.object(installer.subprocess, "run") as run,
            ):
                self.assertFalse(
                    installer._delegate_system_installation(
                        args, {"native": ["ruff"]}, []
                    )
                )
            run.assert_not_called()

    def test_default_lifecycle_stops_if_runtime_installation_fails(self) -> None:
        with patch.object(
            installer,
            "_apply_environment",
            side_effect=[0, subprocess.CalledProcessError(1, "install")],
        ) as apply:
            with self.assertRaises(subprocess.CalledProcessError):
                installer.main(["install-environment", "repository-devcontainer"])
        self.assertEqual(
            [call.args[0].phase for call in apply.call_args_list], ["build", "runtime"]
        )

    def test_apt_tool_setup_is_retained_when_installation_is_delegated(self) -> None:
        # Java is selected through APT, but also needs java.sh to set JAVA_HOME.
        # Both an image build and a normal user must execute that setup.
        for uid in (0, 1000):
            with (
                self.subTest(uid=uid),
                patch.object(installer.os, "geteuid", return_value=uid),
                patch.object(
                    installer,
                    "load_environments",
                    return_value={"java-only": {"apt": ["openjdk"]}},
                ),
                patch.object(installer.subprocess, "run") as run,
            ):
                installer.main(
                    [
                        "install-environment",
                        "java-only",
                        "--os",
                        "linux",
                        "--cpu",
                        "arm64",
                    ]
                )
                commands = [call.args[0] for call in run.call_args_list]
                if uid == 0:
                    self.assertEqual(commands[0][0], "apt-get")
                    self.assertEqual(commands[1][0], "bash")
                    self.assertEqual(Path(commands[1][1]).name, "java.sh")
                else:
                    self.assertEqual(len(commands), 1)
                    self.assertEqual(commands[0][0], "sudo")
                    self.assertEqual(
                        commands[0][commands[0].index("--providers") + 1 :],
                        ["apt", "setup"],
                    )

    def test_native_only_installation_skips_apt_even_if_selection_has_build_packages(
        self,
    ) -> None:
        # s-core-local includes APT build dependencies for special setup. A user
        # requesting only native tools must not install or purge those packages.
        with tempfile.TemporaryDirectory() as directory:
            for phase in ("all", "build", "cleanup"):
                with (
                    self.subTest(phase=phase),
                    patch.object(installer.os, "geteuid", return_value=1000),
                    patch.object(installer, "_cmd_install") as native,
                    patch.object(installer.subprocess, "run") as run,
                ):
                    installer.main(
                        [
                            "install-environment",
                            "s-core-local",
                            "--destination",
                            directory,
                            "--os",
                            "linux",
                            "--cpu",
                            "arm64",
                            "--phase",
                            phase,
                            "--providers",
                            "native",
                        ]
                    )
                    run.assert_not_called()
                    self.assertEqual(native.call_count, 1 if phase == "all" else 0)

    def test_python_dependency_and_build_only_phase_are_validated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "environments.json"
            with patch.object(catalog, "ENVIRONMENTS_PATH", path):
                for data, message in (
                    ({"ci": {"python": ["pre-commit"]}}, "requires 'uv'"),
                    ({"ci": {"apt": ["zstd"]}}, "Wrong installation phase"),
                    (
                        {"ci": {"setup": ["codeql_coding_standards"]}},
                        "requires 'codeql'",
                    ),
                ):
                    with self.subTest(data=data):
                        path.write_text(json.dumps(data))
                        with self.assertRaisesRegex(SystemExit, message):
                            catalog.load_environments()

    def test_special_setup_uses_membership_and_owned_bundle_items(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = self._copy_tools(root)
            installer = tools / "internal/devcontainer/install.py"

            def run(*args):
                return subprocess.run(
                    [sys.executable, "-I", "-B", str(installer), *args],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )

            self.assertEqual(run("selected", "s-core-local", "codeql").returncode, 0)
            selection_path = tools / "environments.json"
            selections = json.loads(selection_path.read_text())
            selections["s-core-local"]["setup"] = []
            selection_path.write_text(json.dumps(selections))
            self.assertEqual(run("selected", "s-core-local", "codeql").returncode, 1)
            packs = run("items", "codeql_coding_standards", "packs")
            self.assertEqual(packs.returncode, 0, packs.stderr)
            definitions = json.loads((tools / "providers.json").read_text())
            self.assertEqual(
                packs.stdout.splitlines(),
                definitions["codeql_coding_standards"]["packs"],
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

    def test_missing_codeql_build_dependency_is_rejected_before_build(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = self._copy_tools(root)
            path = tools / "environments.json"
            selections = json.loads(path.read_text())
            selections["s-core-local"]["build-apt"].remove("zstd")
            path.write_text(json.dumps(selections))
            marker = root / "apt-was-called"
            fake_bin = root / "fake-bin"
            fake_bin.mkdir()
            apt = fake_bin / "apt-get"
            apt.write_text(f"#!/bin/sh\ntouch '{marker}'\n")
            apt.chmod(0o755)
            environment = dict(
                os.environ, PATH=str(fake_bin) + os.pathsep + os.environ["PATH"]
            )
            result = self._run(
                tools,
                root,
                "s-core-local",
                root / "bin",
                "--phase",
                "build",
                env=environment,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Tool 'codeql' requires 'zstd'", result.stderr)
            self.assertFalse(marker.exists())

    def test_declared_setup_receives_metadata_without_changing_the_parent_shell(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = self._copy_tools(root)
            provider = {
                "provider": "release",
                "version": "a 'literal' value",
                "platforms": ["linux/arm64"],
                "setup_script": "fixture.sh",
            }
            providers_path = tools / "providers.json"
            providers_path.write_text(json.dumps({"fixture": provider}))
            selections_path = tools / "environments.json"
            selections_path.write_text(json.dumps({"ci": {"setup": ["fixture"]}}))
            script = tools / "internal/devcontainer/setup/fixture.sh"
            script.write_text(
                'printf "%s\\n" "$fixture_version" "$SCORE_TOOL_ENVIRONMENT" > "$SCORE_TEST_OUTPUT"\n'
            )
            output = root / "setup-output"
            environment = dict(os.environ, SCORE_TEST_OUTPUT=str(output))
            result = self._run(tools, root, "ci", root / "bin", env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                output.read_text().splitlines(), [provider["version"], "ci"]
            )
            output.unlink()
            # An explicitly unsupported platform must skip this setup script.
            # Removing the tool from the selection must also stop it running.
            provider["platforms"] = ["linux/x86_64"]
            provider["omissions"] = {"linux/arm64": "Fixture has no ARM artifact"}
            providers_path.write_text(json.dumps({"fixture": provider}))
            result = self._run(tools, root, "ci", root / "bin", env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(output.exists())
            selections_path.write_text(json.dumps({"ci": {"setup": []}}))
            result = self._run(tools, root, "ci", root / "bin", env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(output.exists())

    def test_volume_setup_prepares_writable_user_parent_directories(self) -> None:
        # Docker can create .local as root when mounting a volume below it.
        # Its owner must be fixed so the user can create sibling state directories.
        script = (
            TOOLS_DIR.parent
            / "src/s-core-devcontainer/.devcontainer/s-core-local/fix_config_volume_ownership.sh"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "home"
            fake_bin = root / "bin"
            fake_bin.mkdir()
            for name in (".config/opencode", ".config/gh", ".local/share/opencode"):
                (home / name).mkdir(parents=True, exist_ok=True)
            private_directories = (home / ".config", home / ".local")
            for path in private_directories:
                path.chmod(0o700)
            sudo = fake_bin / "sudo"
            sudo.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$@" >> "$SCORE_TEST_LOG"\nexec "$@"\n'
            )
            sudo.chmod(0o755)
            log = root / "calls"
            result = subprocess.run(
                ["bash", str(script)],
                env=dict(
                    os.environ,
                    HOME=str(home),
                    PATH=str(fake_bin) + os.pathsep + os.environ["PATH"],
                    SCORE_TEST_LOG=str(log),
                ),
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = log.read_text().splitlines()
            self.assertEqual(calls[0], "mkdir")
            self.assertIn("chown", calls)
            for path in private_directories:
                self.assertEqual(path.stat().st_mode & 0o777, 0o700)
            for name in (".config", ".local", ".local/share"):
                self.assertIn(str(home / name), calls)

    def _copy_tools(self, root: Path) -> Path:
        tools = root / "copied-tools"
        shutil.copytree(TOOLS_DIR, tools, ignore=shutil.ignore_patterns("__pycache__"))
        return tools

    def _run(
        self,
        tools: Path,
        cwd: Path,
        environment: str,
        destination: Path,
        *arguments,
        env=None,
    ):
        # Simulate sudo for isolated integration tests: child commands may write
        # only fixture paths and use fake apt/npm executables, never host packages.
        fake_bin = cwd / "sudo-bin"
        fake_bin.mkdir(exist_ok=True)
        sudo = fake_bin / "sudo"
        sudo.write_text(
            f"#!{sys.executable}\n"
            "import os, runpy, sys\n"
            "from unittest.mock import patch\n"
            "os.environ['SCORE_TEST_PRIVILEGED'] = '1'\n"
            "sys.argv = sys.argv[2:]\n"
            "with patch('os.geteuid', return_value=0):\n"
            "    runpy.run_path(sys.argv[0], run_name='__main__')\n"
        )
        sudo.chmod(0o755)
        env = dict(os.environ if env is None else env)
        env["PATH"] = str(fake_bin) + os.pathsep + env["PATH"]
        return subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(tools / "internal/devcontainer/install.py"),
                "install-environment",
                environment,
                "--destination",
                str(destination),
                "--os",
                "linux",
                "--cpu",
                "arm64",
                *arguments,
            ],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
