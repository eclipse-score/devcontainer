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
"""Provision a direct host tool prefix from the aqua and Python owners."""

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from hashlib import sha256


TOOLS_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = TOOLS_DIR.parent if TOOLS_DIR.name == "tools" else None
DEFAULT_OWNER_DIR = (
    REPOSITORY_ROOT / "tools/owners/aqua"
    if REPOSITORY_ROOT is not None
    else Path("/tmp/score-tool-owner")
)
PYTHON_CATALOG = TOOLS_DIR / "score_tools/python_tools.bzl"
OWNER_INPUTS = (
    "aqua.yaml",
    "aqua-policy.yaml",
    "aqua-bootstrap.toml",
    "aqua-checksums.json",
    "apm-registry.yaml",
    "starpls-registry.yaml",
    "pyproject.toml",
)
STATE_SCHEMA_VERSION = 1


def _requirements(groups: dict, group: str) -> list[str]:
    """Flatten selected dependency groups without creating another version list."""
    result: list[str] = []
    active: set[str] = set()

    def visit(name: str) -> None:
        if name in active:
            raise SystemExit(f"Recursive Python dependency group: {name}")
        try:
            entries = groups[name]
        except KeyError as exc:
            raise SystemExit(f"Unknown Python dependency group: {name}") from exc
        active.add(name)
        for entry in entries:
            if isinstance(entry, dict) and set(entry) == {"include-group"}:
                visit(entry["include-group"])
            elif isinstance(entry, str) and "==" in entry:
                result.append(entry)
            else:
                raise SystemExit(
                    f"Unsupported pinned dependency in group {name}: {entry!r}"
                )
        active.remove(name)

    visit(group)
    return result


def _copy_selected_aqua_commands(
    aqua: str,
    config: Path,
    profile: str,
    commands: list[str],
    prefix: Path,
    prefix_bin: Path,
    environment: dict,
) -> None:
    """Expose only selected Aqua commands, even if cp emits extra files."""
    if not commands:
        return

    with tempfile.TemporaryDirectory(prefix=".score-tools-aqua-", dir=prefix) as temp:
        staging = Path(temp)
        subprocess.run(
            [
                aqua,
                "-c",
                str(config),
                "cp",
                "--tags",
                profile,
                "-o",
                str(staging),
                *commands,
            ],
            check=True,
            env=environment,
        )
        selected = {name: staging / name for name in commands}
        missing = sorted(
            name
            for name, path in selected.items()
            if not path.is_file() or not os.access(path, os.X_OK)
        )
        if missing:
            raise SystemExit(
                "Aqua did not copy selected executable commands: " + ", ".join(missing)
            )

        for name, source in selected.items():
            os.replace(source, prefix_bin / name)


def _python_catalog() -> dict:
    """Read command identities from the generated compatibility catalog."""
    module = ast.parse(PYTHON_CATALOG.read_text(encoding="utf-8"))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target, ast.Name) and target.id == "PYTHON_TOOLS"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, dict):
                return value
    raise SystemExit(f"Cannot read PYTHON_TOOLS from {PYTHON_CATALOG}")


def _copy_apm_runtime(
    aqua: str, owner_dir: Path, prefix: Path, environment: dict
) -> None:
    """Keep APM's adjacent frozen-Python runtime while exposing its raw binary."""
    config = owner_dir / "aqua.yaml"
    subprocess.run(
        [aqua, "-c", str(config), "install", "--tags", "published"],
        check=True,
        env=environment,
    )
    resolved = subprocess.run(
        [aqua, "-c", str(config), "which", "apm"],
        check=True,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    binary = Path(resolved).resolve()
    if binary.name != "apm" or not binary.is_file():
        raise SystemExit(f"Aqua did not resolve the APM runtime binary: {resolved}")

    runtime = prefix / "lib/apm"
    if runtime.exists():
        shutil.rmtree(runtime)
    runtime.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(binary.parent, runtime, symlinks=True)
    link = prefix / "bin/apm"
    link.unlink(missing_ok=True)
    link.symlink_to("../lib/apm/apm")


def _owner_digest(owner_dir: Path) -> str:
    """Fingerprint the inputs that determine the provisioned command set."""
    digest = sha256()
    for name in (*OWNER_INPUTS, "python_tools.bzl"):
        source = PYTHON_CATALOG if name == "python_tools.bzl" else owner_dir / name
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(source.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _expected_commands(
    profile: str, aqua_config: str, requirements: list[str], definitions: dict
) -> list[str]:
    """Return selected command paths needed to trust an existing prefix."""
    commands = _native_commands(profile, aqua_config)
    commands.update(_expected_python_commands(requirements, definitions))
    return sorted(commands)


def _native_commands(profile: str, aqua_config: str) -> set[str]:
    """Return the names selected from Aqua, including uv's uvx command."""
    commands = set()
    for block in re.split(r"(?m)^\s*-\s+name:\s+", aqua_config)[1:]:
        name, _, body = block.partition("\n")
        if re.search(r"(?m)^\s*-\s+" + re.escape(profile) + r"\s*$", body):
            commands.add(name.rsplit("@", 1)[0].rsplit("/", 1)[-1])
    if "uv" in commands:
        commands.add("uvx")
    return commands


def _expected_python_commands(requirements: list[str], definitions: dict) -> set[str]:
    """Return every catalogued console script exposed by selected Python tools."""
    commands = set()
    for requirement in requirements:
        name = requirement.split("==", 1)[0]
        definition = definitions.get(name)
        if definition is None or definition.get("package") != name:
            raise SystemExit(
                f"Python command identity is missing from {PYTHON_CATALOG}: {name}"
            )
        commands.update(definition.get("entrypoints", [definition["entrypoint"]]))
    return commands


def _command_identity(path: Path) -> dict | None:
    """Fingerprint one exposed command without following its top-level link."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(info.st_mode):
        identity = {"kind": "symlink", "target": os.readlink(path)}
        try:
            target = path.resolve()
            if target.is_file():
                identity["target_sha256"] = _file_sha256(target)
                identity["target_mode"] = stat.S_IMODE(target.stat().st_mode)
        except (OSError, RuntimeError):
            identity["target_error"] = "unresolvable"
        return identity
    if stat.S_ISREG(info.st_mode):
        return {
            "kind": "file",
            "sha256": _file_sha256(path),
            "mode": stat.S_IMODE(info.st_mode),
        }
    return {"kind": "other", "mode": stat.S_IMODE(info.st_mode)}


def _file_sha256(path: Path) -> str:
    """Hash command bytes so replacing a regular file cannot look manager-owned."""
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_state(prefix: Path) -> dict:
    """Load an ownership ledger; never guess at pre-existing command ownership."""
    state_path = prefix / ".score-tools-owner.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": STATE_SCHEMA_VERSION, "profiles": {}}
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid host tool ownership state: {state_path}") from exc
    if (
        isinstance(state, dict)
        and state.get("schema_version") == STATE_SCHEMA_VERSION
        and isinstance(state.get("profiles"), dict)
    ):
        for record in state["profiles"].values():
            if not isinstance(record, dict) or not isinstance(
                record.get("commands"), dict
            ):
                break
            if any(
                not isinstance(identity, dict)
                for identity in record["commands"].values()
            ):
                break
        else:
            return state
    raise SystemExit(
        f"Host tool prefix has no supported ownership ledger: {state_path}. "
        "Use a fresh --prefix so command ownership can be recorded safely."
    )


def _prefix_is_current(
    prefix: Path,
    profile: str,
    owner_digest: str,
    commands: list[str],
    state: dict,
) -> bool:
    record = state.get("profiles", {}).get(profile)
    if not isinstance(record, dict) or record.get("owner_digest") != owner_digest:
        return False
    recorded = record.get("commands")
    if not isinstance(recorded, dict) or set(recorded) != set(commands):
        return False
    return all(
        os.access(prefix / "bin" / command, os.X_OK)
        and _command_identity(prefix / "bin" / command) == recorded[command]
        for command in commands
    )


def _validate_selected_paths(prefix: Path, commands: list[str], state: dict) -> None:
    """Refuse to replace a foreign command or one whose saved identity changed."""
    owners: dict[str, list[dict]] = {}
    for profile in state.get("profiles", {}).values():
        for name, identity in profile.get("commands", {}).items():
            owners.setdefault(name, []).append(identity)
    for name in commands:
        if Path(name).name != name:
            raise SystemExit(f"Invalid selected command path: {name!r}")
        command = prefix / "bin" / name
        current = _command_identity(command)
        if current is None:
            continue
        if current not in owners.get(name, []):
            raise SystemExit(
                f"Refusing to replace unmanaged or user-replaced command: {command}"
            )


def _write_state(prefix: Path, state: dict) -> None:
    """Atomically replace the ownership ledger after command reconciliation."""
    path = prefix / ".score-tools-owner.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _reconcile_commands(
    prefix: Path,
    state: dict,
    desired_by_profile: dict[str, list[str]],
    profile: str,
    owner_digest: str,
    commands: list[str],
) -> list[str]:
    """Retire only unchanged owned exposures with no remaining profile owner."""
    old_profiles = state.get("profiles", {})
    retained: dict[str, dict] = {}
    for name, record in old_profiles.items():
        desired = set(desired_by_profile.get(name, []))
        kept = {
            command: identity
            for command, identity in record.get("commands", {}).items()
            if command in desired
        }
        if kept:
            retained[name] = {
                "owner_digest": record.get("owner_digest"),
                "commands": kept,
            }

    actual: dict[str, dict] = {}
    for command in commands:
        identity = _command_identity(prefix / "bin" / command)
        if identity is None or not os.access(prefix / "bin" / command, os.X_OK):
            raise SystemExit(
                f"Provisioned command is missing or not executable: {command}"
            )
        actual[command] = identity

    # Commands shared by several profiles occupy one path. A successful refresh
    # updates the saved identity for every profile that still selects that path.
    for record in retained.values():
        for command in record["commands"]:
            if command in actual:
                record["commands"][command] = actual[command]
    retained[profile] = {
        "owner_digest": owner_digest,
        "commands": {name: actual[name] for name in commands},
    }

    prior_identities: dict[str, list[dict]] = {}
    for record in old_profiles.values():
        for name, identity in record.get("commands", {}).items():
            prior_identities.setdefault(name, []).append(identity)
    still_owned = {name for record in retained.values() for name in record["commands"]}
    removed = []
    for name, identities in prior_identities.items():
        if name in still_owned:
            continue
        path = prefix / "bin" / name
        current = _command_identity(path)
        if current is not None and current in identities:
            path.unlink()
            removed.append(name)

    updated = {"schema_version": STATE_SCHEMA_VERSION, "profiles": retained}
    _write_state(prefix, updated)
    state.clear()
    state.update(updated)
    return sorted(removed)


def provision(profile: str, prefix: Path, owner_dir: Path) -> None:
    owner_dir = owner_dir.resolve()
    prefix = prefix.resolve()
    prefix.mkdir(parents=True, exist_ok=True)
    config = owner_dir / "aqua.yaml"
    groups = tomllib.loads((owner_dir / "pyproject.toml").read_text(encoding="utf-8"))[
        "dependency-groups"
    ]
    requirements = _requirements(groups, profile)
    definitions = _python_catalog()
    owner_digest = _owner_digest(owner_dir)
    aqua_config = config.read_text(encoding="utf-8")
    expected_commands = _expected_commands(
        profile, aqua_config, requirements, definitions
    )
    state = _read_state(prefix)
    if _prefix_is_current(prefix, profile, owner_digest, expected_commands, state):
        print(
            json.dumps(
                {
                    "status": "current",
                    "profile": profile,
                    "prefix": str(prefix),
                    "bin": str(prefix / "bin"),
                },
                indent=2,
            )
        )
        return

    desired_by_profile = {
        name: _expected_commands(
            name,
            aqua_config,
            _requirements(groups, name),
            definitions,
        )
        for name in groups
    }
    _validate_selected_paths(prefix, expected_commands, state)

    aqua = os.environ.get("AQUA_BINARY")
    if aqua is None:
        bootstrap = tomllib.loads(
            (owner_dir / "aqua-bootstrap.toml").read_text(encoding="utf-8")
        )
        bootstrap_path = prefix / "bootstrap" / f"aqua-{bootstrap['version']}" / "aqua"
        if not os.access(bootstrap_path, os.X_OK):
            from bootstrap_aqua import bootstrap as install_aqua_bootstrap

            install_aqua_bootstrap(bootstrap_path.parent, owner_dir=owner_dir)
        aqua = str(bootstrap_path)
    prefix_bin = prefix / "bin"
    prefix_bin.mkdir(parents=True, exist_ok=True)

    environment = os.environ.copy()
    environment["AQUA_POLICY_CONFIG"] = str(owner_dir / "aqua-policy.yaml")
    environment.setdefault("AQUA_ROOT_DIR", str(prefix / ".aqua"))
    _copy_selected_aqua_commands(
        aqua,
        config,
        profile,
        sorted(_native_commands(profile, aqua_config)),
        prefix,
        prefix_bin,
        environment,
    )

    if profile == "published":
        _copy_apm_runtime(aqua, owner_dir, prefix, environment)

    uv = prefix_bin / "uv"
    if requirements and not uv.is_file():
        raise SystemExit(f"Aqua did not provision the selected uv binary: {uv}")
    environment["UV_TOOL_DIR"] = str(prefix / "uv/tools")
    staged_commands: dict[str, Path] = {}
    with tempfile.TemporaryDirectory(prefix=".score-tools-bin-", dir=prefix) as staging:
        staging_root = Path(staging)
        for requirement in requirements:
            package = requirement.split("==", 1)[0]
            package_bin = staging_root / package
            package_bin.mkdir()
            environment["UV_TOOL_BIN_DIR"] = str(package_bin)
            subprocess.run(
                [str(uv), "--no-config", "tool", "install", "--force", requirement],
                check=True,
                env=environment,
            )
            for command in package_bin.iterdir():
                if command.name in staged_commands:
                    raise SystemExit(
                        f"Several selected Python tools expose {command.name!r}"
                    )
                staged_commands[command.name] = command

        expected_python = _expected_python_commands(requirements, definitions)
        if set(staged_commands) != expected_python:
            unexpected = sorted(set(staged_commands) - expected_python)
            missing = sorted(expected_python - set(staged_commands))
            raise SystemExit(
                "Python console-script catalog differs from uv output; "
                f"unexpected={unexpected}, missing={missing}"
            )
        _validate_selected_paths(prefix, sorted(expected_python), state)
        for name, staged in staged_commands.items():
            destination = prefix_bin / name
            if destination.exists() or destination.is_symlink():
                destination.unlink()
            os.replace(staged, destination)

    missing = [
        command
        for command in expected_commands
        if not os.access(prefix_bin / command, os.X_OK)
    ]
    if missing:
        raise SystemExit(
            "Provisioned prefix is missing selected commands: " + ", ".join(missing)
        )
    removed = _reconcile_commands(
        prefix,
        state,
        desired_by_profile,
        profile,
        owner_digest,
        expected_commands,
    )

    print(
        json.dumps(
            {
                "status": "provisioned",
                "profile": profile,
                "prefix": str(prefix),
                "bin": str(prefix_bin),
                "python_requirements": requirements,
                "retired_commands": removed,
            },
            indent=2,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile", choices=("repository", "published"), default="repository"
    )
    parser.add_argument(
        "--prefix",
        type=Path,
        default=Path.home() / ".local/share/score-tools",
    )
    parser.add_argument(
        "--owner-dir",
        type=Path,
        default=DEFAULT_OWNER_DIR,
        help="Production tool owner directory (defaults to tools/owners/aqua).",
    )
    args = parser.parse_args()
    provision(args.profile, args.prefix, args.owner_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
