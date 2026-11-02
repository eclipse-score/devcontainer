#!/usr/bin/env python3
# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Install selected mise-owned tools once and expose their direct executables."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import tomllib

TOOLS_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = TOOLS_ROOT.parent
OWNER_ROOT = TOOLS_ROOT / "mise"
BOOTSTRAP = Path(__file__).with_name("bootstrap.sh")
DATA_DIR = Path("/opt/score-tools/mise-data")
MISE_DIR = Path("/opt/score-tools/mise")

# Native backend names are the small adapter boundary between environment
# membership and the owner's config keys. Versions remain in mise TOML.
NATIVE_BACKENDS = {
    "actionlint": "aqua:rhysd/actionlint",
    "apm": "github:microsoft/apm",
    "bazelisk": "aqua:bazelbuild/bazelisk",
    "buildifier": "aqua:bazelbuild/buildtools/buildifier",
    "opencode": "aqua:anomalyco/opencode",
    "ruff": "aqua:astral-sh/ruff",
    "shellcheck": "aqua:koalaman/shellcheck",
    "starpls": "github:withered-magic/starpls",
    "uv": "uv",
    "uvx": "uv",
    "yamlfmt": "aqua:google/yamlfmt",
}

OWNER_FILES = {
    "native": "mise.native.toml",
    "python": "mise.python.toml",
    "published": "mise.published.toml",
}
OWNERSHIP_FILE = ".score-mise-ownership.json"
LOCK_FILE = ".score-mise-provision.lock"


def _owner_tools(owner_root: Path) -> dict[str, dict[str, str]]:
    tools: dict[str, dict[str, str]] = {}
    for profile, filename in OWNER_FILES.items():
        path = owner_root / filename
        with path.open("rb") as handle:
            entries = tomllib.load(handle).get("tools", {})
        for backend, version in entries.items():
            if backend in tools:
                raise SystemExit(f"mise backend is declared more than once: {backend}")
            if not isinstance(version, str) or not version:
                raise SystemExit(f"Invalid mise pin for {backend}: {version!r}")
            tools[backend] = {"profile": profile, "version": version}
    return tools


def _requested_tools(environment: str, owner_root: Path) -> dict[str, dict[str, str]]:
    sys.path.insert(0, str(TOOLS_ROOT))
    from score_tools.catalog import (
        _load_python_tools,
        load_catalog_versions,
        load_environments,
    )

    try:
        selection = load_environments()[environment]
    except KeyError as exc:
        raise SystemExit(f"Unknown tool environment: {environment}") from exc
    owners = _owner_tools(owner_root)
    python_tools = _load_python_tools()
    catalog_versions = load_catalog_versions()
    requested: dict[str, dict[str, str]] = {}

    for name in selection.get("native", []):
        backend = NATIVE_BACKENDS.get(name)
        if backend is None:
            raise SystemExit(
                f"No mise backend mapping for selected native tool: {name}"
            )
        owner = owners.get(backend)
        if owner is None:
            raise SystemExit(
                f"Selected native tool {name} has no mise owner: {backend}"
            )
        if catalog_versions.get(name) != owner["version"]:
            raise SystemExit(
                f"Generated native metadata for {name} is stale: "
                f"catalog={catalog_versions.get(name)}, mise={owner['version']}"
            )
        requested[name] = {**owner, "backend": backend, "entrypoint": name}

    for name in selection.get("python", []):
        metadata = python_tools.get(name)
        if metadata is None:
            raise SystemExit(
                f"Selected Python tool is missing from the catalog: {name}"
            )
        backend = "pypi:" + metadata["package"]
        owner = owners.get(backend)
        if owner is None:
            raise SystemExit(
                f"Selected Python tool {name} has no mise owner: {backend}"
            )
        if metadata["version"] != owner["version"]:
            raise SystemExit(
                f"Generated Python pin for {name} is stale: catalog={metadata['version']}, "
                f"mise={owner['version']}"
            )
        requested[name] = {
            **owner,
            "backend": backend,
            "entrypoint": metadata["entrypoint"],
        }

    if "uv" in selection.get("native", []) and "uvx" in selection.get("native", []):
        owner = owners[NATIVE_BACKENDS["uv"]]
        requested["uvx"] = {
            **owner,
            "backend": NATIVE_BACKENDS["uv"],
            "entrypoint": "uvx",
        }
    return requested


def _environment(owner_root: Path, data_dir: Path) -> dict[str, str]:
    state_dir = data_dir.parent / "mise-state"
    environment = os.environ.copy()
    environment.update(
        MISE_CACHE_DIR=str(state_dir / "cache"),
        MISE_CONFIG_DIR=str(state_dir / "config"),
        MISE_DATA_DIR=str(data_dir),
        MISE_STATE_DIR=str(state_dir / "state"),
        MISE_SYSTEM_CONFIG_DIR=str(state_dir / "system-config"),
        MISE_YES="1",
        MISE_TRUSTED_CONFIG_PATHS=str(owner_root),
    )
    if Path("/usr/bin/python3").is_file():
        environment.setdefault("UV_PYTHON", "/usr/bin/python3")
        environment.setdefault("UV_PYTHON_PREFERENCE", "only-system")
    return environment


def _mise_binary(path: Path | None) -> Path:
    if path is not None:
        binary = path
    elif os.environ.get("MISE_BINARY"):
        binary = Path(os.environ["MISE_BINARY"])
    else:
        binary = MISE_DIR / "mise"
        subprocess.run(["bash", str(BOOTSTRAP), str(MISE_DIR)], check=True)
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise SystemExit(f"mise executable missing or not executable: {binary}")
    return binary


def _run(
    mise: Path,
    owner_root: Path,
    profile: str,
    action: str,
    backends: list[str],
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(mise), "-C", str(owner_root), "-E", profile, action, *backends],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )


def _find_entrypoint(install_root: Path, name: str) -> Path:
    direct = install_root / name
    if direct.is_file() and os.access(direct, os.X_OK):
        return direct
    matches = sorted(
        {
            path.resolve()
            for path in install_root.rglob(name)
            if path.is_file() and os.access(path, os.X_OK)
        }
    )
    if len(matches) != 1:
        raise SystemExit(
            f"Expected one executable named {name} under {install_root}; found {matches}"
        )
    return matches[0]


@contextmanager
def _ownership_lock(bin_dir: Path):
    """Serialize link reconciliation for environments sharing one bin dir."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    with (bin_dir / LOCK_FILE).open("a", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _read_ownership(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(
            f"Cannot read mise command ownership state {path}: {exc}"
        ) from exc
    if (
        not isinstance(state, dict)
        or state.get("schema") != 1
        or not isinstance(state.get("environments"), dict)
    ):
        raise SystemExit(f"Unsupported mise command ownership state: {path}")
    environments = state["environments"]
    if any(
        not isinstance(environment, str)
        or not isinstance(commands, dict)
        or any(
            not isinstance(name, str)
            or not name
            or Path(name).name != name
            or not isinstance(target, str)
            or not Path(target).is_absolute()
            for name, target in commands.items()
        )
        for environment, commands in environments.items()
    ):
        raise SystemExit(f"Malformed mise command ownership state: {path}")
    return environments


def _write_ownership(path: Path, environments: dict[str, dict[str, str]]) -> None:
    state = json.dumps({"schema": 1, "environments": environments}, indent=2) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(state)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _link_is_owned(link: Path, target: str) -> bool:
    """Only retire the exact symlink recorded by this provisioner."""
    return link.is_symlink() and os.readlink(link) == target


def reconcile_commands(
    environment_name: str,
    installed: dict[str, Path],
    bin_dir: Path,
) -> None:
    """Replace one environment's links while preserving other owners and users.

    A persistent per-bin ownership map makes repeated feature installation
    composable: updating one selection cannot remove another selection's
    command. A deselected path is unlinked only while it is still the exact
    symlink this provisioner recorded. Replaced paths are preserved and called
    out so an operator can decide whether to keep them.
    """
    state_path = bin_dir / OWNERSHIP_FILE
    with _ownership_lock(bin_dir):
        environments = _read_ownership(state_path)
        previous = environments.pop(environment_name, {})
        others: dict[str, dict[str, str]] = {}
        for owner, commands in environments.items():
            for name, target in commands.items():
                others.setdefault(name, {})[owner] = target

        selected = {name: str(target.resolve()) for name, target in installed.items()}
        for name, target in selected.items():
            other_targets = set(others.get(name, {}).values())
            if other_targets and other_targets != {target}:
                owners = ", ".join(sorted(others[name]))
                raise SystemExit(
                    f"Cannot expose {name} for {environment_name}: it is already "
                    f"owned by {owners} at a different mise installation"
                )
            link = bin_dir / name
            recorded = previous.get(name)
            owned_targets = [*others.get(name, {}).values()]
            if recorded is not None:
                owned_targets.append(recorded)
            if os.path.lexists(link) and not any(
                _link_is_owned(link, owned_target) for owned_target in owned_targets
            ):
                raise SystemExit(
                    f"Refusing to replace unmanaged or user-replaced command: {link}"
                )

        selected_names = set(selected)
        for name, target in previous.items():
            if name in selected_names or name in others:
                continue
            link = bin_dir / name
            if _link_is_owned(link, target):
                link.unlink()
            elif os.path.lexists(link):
                print(
                    f"Preserving user-replaced command {link}; no longer owned by "
                    f"{environment_name}",
                    file=sys.stderr,
                )

        for name, target in selected.items():
            link = bin_dir / name
            if _link_is_owned(link, target):
                continue
            for _attempt in range(10):
                temporary = bin_dir / (
                    f".{name}.mise-{os.getpid()}-{secrets.token_hex(8)}"
                )
                try:
                    temporary.symlink_to(target)
                    break
                except FileExistsError:
                    continue
            else:
                raise SystemExit(f"Cannot allocate a temporary command link for {name}")
            try:
                os.replace(temporary, link)
            finally:
                temporary.unlink(missing_ok=True)

        if selected:
            environments[environment_name] = selected
        if environments:
            _write_ownership(state_path, environments)
        else:
            state_path.unlink(missing_ok=True)


def provision(
    environment_name: str,
    *,
    owner_root: Path = OWNER_ROOT,
    data_dir: Path = DATA_DIR,
    bin_dir: Path = Path("/usr/local/bin"),
    mise_binary: Path | None = None,
) -> dict[str, Path]:
    requested = _requested_tools(environment_name, owner_root)
    mise = _mise_binary(mise_binary)
    env = _environment(owner_root, data_dir)
    groups: dict[tuple[str, bool], list[str]] = {}
    for item in requested.values():
        profile = item["profile"]
        python = item["backend"].startswith("pypi:")
        groups.setdefault((profile, python), []).append(item["backend"])

    for (profile, python), backends in groups.items():
        unique_backends = sorted(set(backends))
        command = [
            str(mise),
            "-C",
            str(owner_root),
            "-E",
            profile,
            "install",
        ]
        if not python:
            command.append("--locked")
        command.extend(unique_backends)
        subprocess.run(command, check=True, env=env)
        if profile == "native" and "uv" in unique_backends:
            uv_records = json.loads(
                _run(mise, owner_root, profile, "ls", ["--json"], env).stdout
            ).get("uv", [])
            uv_version = requested["uv"]["version"]
            uv_record = next(
                (
                    record
                    for record in uv_records
                    if record.get("active")
                    and record.get("installed")
                    and record.get("version") == uv_version
                ),
                None,
            )
            if uv_record is None:
                raise SystemExit(f"mise did not resolve selected uv at {uv_version}")
            uv_root = Path(uv_record["install_path"])
            uv_executable = _find_entrypoint(uv_root, "uv")
            env["PATH"] = str(uv_executable.parent) + os.pathsep + env.get("PATH", "")
            # Keep PyPI CLI installation on the pinned mise-managed uv even
            # when the caller's mise settings would otherwise select pipx.
            env["MISE_PYPI_UVX"] = "true"

    installed: dict[str, Path] = {}
    for profile, _python in groups:
        entries = json.loads(
            _run(mise, owner_root, profile, "ls", ["--json"], env).stdout
        )
        profile_names = {
            name: item for name, item in requested.items() if item["profile"] == profile
        }
        for name, item in profile_names.items():
            records = entries.get(item["backend"], [])
            matching = [
                record
                for record in records
                if record.get("active")
                and record.get("installed")
                and record.get("version") == item["version"]
            ]
            if len(matching) != 1:
                raise SystemExit(
                    f"mise did not resolve the selected {name} at {item['version']}"
                )
            install_root = Path(matching[0]["install_path"])
            executable = _find_entrypoint(install_root, item["entrypoint"])
            if not executable.is_absolute():
                raise SystemExit(f"mise returned a relative executable for {name}")
            installed[name] = executable

    reconcile_commands(environment_name, installed, bin_dir)
    for name, executable in installed.items():
        print(f"{name} {requested[name]['version']} -> {executable}")
    return installed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install one declared environment and expose direct pinned commands."
    )
    parser.add_argument(
        "environment", choices=("s-core-local", "bazel-feature", "repository")
    )
    parser.add_argument("--owner-root", type=Path, default=OWNER_ROOT)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--bin-dir", type=Path, default=Path("/usr/local/bin"))
    parser.add_argument("--mise", type=Path)
    args = parser.parse_args()
    provision(
        args.environment,
        owner_root=args.owner_root,
        data_dir=args.data_dir,
        bin_dir=args.bin_dir,
        mise_binary=args.mise,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
