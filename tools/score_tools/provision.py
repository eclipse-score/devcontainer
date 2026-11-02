# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Provision once from portable owners; publish ordinary direct command links."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

from score_tools.catalog import _load_python_tools, load_native_tools

TOOLS_ROOT = Path(__file__).resolve().parents[1]


def host_platform() -> tuple[str, str]:
    systems = {"Linux": "linux", "Darwin": "macos"}
    cpus = {"x86_64": "x86_64", "amd64": "x86_64", "arm64": "arm64", "aarch64": "arm64"}
    try:
        return systems[platform.system()], cpus[platform.machine().lower()]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported platform: {platform.system()}/{platform.machine()}"
        ) from exc


def _name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value):
        raise ValueError(f"Invalid command/profile name: {value!r}")
    return value


def select_binary(data: dict, os_name: str, cpu: str) -> dict:
    matches = [b for b in data["binaries"] if (b["os"], b["cpu"]) == (os_name, cpu)]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one binary for {os_name}/{cpu}; found {len(matches)}"
        )
    binary = matches[0]
    if not re.fullmatch(r"[a-f0-9]{64}", binary["sha256"]):
        raise ValueError("Artifact must declare a SHA256 digest")
    return binary


def _relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Unsafe archive path: {value!r}")
    return path


def unpack(binary: dict, archive: Path, destination: Path, command: str) -> None:
    """Extract files only, rejecting traversal and links before writing a tree."""
    kind = binary["kind"]
    if kind == "file":
        shutil.copyfile(archive, destination / command)
    elif kind == "archive" and "dir" in binary:
        prefix = _relative(binary["dir"])
        with tarfile.open(archive) as source:
            entries = []
            for member in source.getmembers():
                path = _relative(member.name)
                if not path.is_relative_to(prefix) or path == prefix:
                    continue
                if not (member.isdir() or member.isfile()):
                    raise ValueError(
                        f"Unsupported archive link/special member: {member.name}"
                    )
                entries.append((member, destination / str(path.relative_to(prefix))))
            if not entries:
                raise ValueError(f"Archive directory not found: {prefix}")
            for member, target in entries:
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with (
                        source.extractfile(member) as reader,
                        target.open("wb") as writer,
                    ):
                        shutil.copyfileobj(reader, writer)
                    target.chmod(0o755 if member.mode & 0o111 else 0o644)
    elif kind == "archive":
        member = str(_relative(binary["file"]))
        if binary.get("type") == "zip":
            with zipfile.ZipFile(archive) as source:
                (destination / command).write_bytes(source.read(member))
        elif binary.get("type") in ("tar.gz", "tgz", "tar.xz", "txz"):
            with tarfile.open(archive) as source:
                info = source.getmember(member)
                if not info.isfile():
                    raise ValueError(f"Expected regular archive member: {member}")
                with (
                    source.extractfile(info) as reader,
                    (destination / command).open("wb") as writer,
                ):
                    shutil.copyfileobj(reader, writer)
        else:
            raise ValueError(f"Unsupported archive type: {binary.get('type')}")
    else:
        raise ValueError(f"Unsupported artifact kind: {kind}")
    target = destination / command
    if not target.is_file():
        raise ValueError(f"Archive did not supply command: {command}")
    target.chmod(0o755)


def _identity(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def download(url: str, destination: Path) -> None:
    for attempt in range(1, 4):
        try:
            with (
                urllib.request.urlopen(url, timeout=60) as source,
                destination.open("wb") as output,
            ):
                shutil.copyfileobj(source, output)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt == 3:
                raise
            print(
                f"Artifact download attempt {attempt}/3 failed: {exc}; retrying",
                file=sys.stderr,
            )
            time.sleep(2)


def install_native(
    command: str,
    data: dict,
    packages: Path,
    system: tuple[str, str],
    *,
    companions: dict[str, dict] | None = None,
) -> Path:
    binary = select_binary(data, *system)
    records = companions or {command: binary}
    for name in records:
        _name(name)
    identity = _identity(records)
    slot = packages / f"artifact-{identity}"
    marker = slot / ".complete"
    if marker.is_file() and marker.read_text() == identity:
        target = slot / command
        if not target.is_file() or not os.access(target, os.X_OK):
            raise ValueError(
                f"Incomplete prepared package: {slot}; use a fresh data directory"
            )
        return target
    if slot.exists():
        raise ValueError(
            f"Unfinished/unowned package directory: {slot}; use a fresh data directory"
        )
    packages.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=packages) as temporary:
        staging = Path(temporary)
        archive = staging / "download"
        download(binary["url"], archive)
        with archive.open("rb") as downloaded:
            actual = hashlib.file_digest(downloaded, "sha256").hexdigest()
        if actual != binary["sha256"]:
            raise ValueError(
                f"Checksum mismatch for {command}: expected {binary['sha256']}, got {actual}"
            )
        tree = staging / "tree"
        tree.mkdir()
        for name, member in records.items():
            unpack(member, archive, tree, name)
        (tree / ".complete").write_text(identity)
        tree.rename(slot)
    return slot / command


def prepare_native(
    command: str, definitions: dict, packages: Path, system: tuple[str, str]
) -> Path:
    binary = select_binary(definitions[command], *system)
    # Commands sharing an archive may rely on adjacent siblings (notably uvx/uv).
    companions = {
        name: candidate
        for name, data in definitions.items()
        for candidate in data["binaries"]
        if (candidate["os"], candidate["cpu"]) == system
        and candidate["url"] == binary["url"]
        and candidate["sha256"] == binary["sha256"]
    }
    return install_native(
        command, definitions[command], packages, system, companions=companions
    )


def install_python(
    requirements: list[str], uv: str, *, bin_dir: Path, tool_dir: Path
) -> None:
    environment = {
        **os.environ,
        "UV_TOOL_BIN_DIR": str(bin_dir),
        "UV_TOOL_DIR": str(tool_dir),
    }
    environment.setdefault("UV_PYTHON", sys.executable)
    for requirement in requirements:
        subprocess.run(
            [uv, "tool", "install", "--force", requirement], env=environment, check=True
        )


def _prepare_python(name: str, data: dict, uv: Path, packages: Path) -> dict[str, Path]:
    slot = packages / f"{_name(name)}-{_identity(data)}"
    marker = slot / ".complete"
    targets = {
        command: slot / "bin" / _name(command)
        for command in [data["entrypoint"], *data.get("aliases", [])]
    }
    if not marker.exists():
        if slot.exists():
            raise ValueError(
                f"Unfinished Python environment: {slot}; use a fresh data directory"
            )
        slot.mkdir(parents=True)
        # uv environments embed absolute paths, so they must be created at their final location.
        install_python(
            [data["package"] + "==" + data["version"]],
            str(uv),
            bin_dir=slot / "bin",
            tool_dir=slot / "tools",
        )
        marker.write_text(_identity(data))
    if marker.read_text() != _identity(data) or any(
        not target.is_file() for target in targets.values()
    ):
        raise ValueError(f"Incomplete prepared Python tool: {slot}")
    return targets


@contextmanager
def locked(bin_dir: Path):
    bin_dir.mkdir(parents=True, exist_ok=True)
    with (bin_dir / ".score-provision.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def publish(installed: dict[str, Path], bin_dir: Path, packages: Path) -> None:
    """Replace only links into this dedicated prepared package tree; never adopt files."""
    for name in installed:
        _name(name)
        path = bin_dir / name
        if os.path.lexists(path) and not (
            path.is_symlink()
            and Path(os.readlink(path)).is_absolute()
            and Path(os.readlink(path)).resolve().is_relative_to(packages.resolve())
            and path.is_file()
        ):
            raise ValueError(f"Refusing unmanaged or user-replaced command: {path}")
    for name, target in installed.items():
        path = bin_dir / name
        if path.is_symlink() and os.readlink(path) == str(target):
            continue
        fd, temporary = tempfile.mkstemp(prefix=".link-", dir=bin_dir)
        os.close(fd)
        Path(temporary).unlink()
        try:
            Path(temporary).symlink_to(target)
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)


def provision(
    profile: str,
    native: list[str],
    python: list[str],
    *,
    bin_dir: Path,
    data_dir: Path,
    root: Path = TOOLS_ROOT,
    system: tuple[str, str] | None = None,
) -> dict[str, Path]:
    bin_dir, data_dir = bin_dir.absolute(), data_dir.absolute()
    _name(profile)
    definitions = load_native_tools(root)
    python_definitions = _load_python_tools(root / "score_tools/python_tools.bzl")
    for name in native:
        select_binary(definitions[name], *(system or host_platform()))
    commands = set(native)
    if len(commands) != len(native) or len(set(python)) != len(python):
        raise ValueError("Duplicate selected tool")
    for name in python:
        data = python_definitions[name]
        for command in [data["entrypoint"], *data.get("aliases", [])]:
            _name(command)
            if command in commands:
                raise ValueError(f"Duplicate selected command: {command}")
            commands.add(command)
    installed = {}
    with locked(bin_dir):
        for name in native:
            installed[name] = prepare_native(
                name,
                definitions,
                data_dir / "packages",
                system or host_platform(),
            )
        if python:
            uv = installed.get("uv") or prepare_native(
                "uv",
                definitions,
                data_dir / "packages",
                system or host_platform(),
            )
            for name in python:
                data = python_definitions[name]
                for command, path in _prepare_python(
                    name, data, uv, data_dir / "packages"
                ).items():
                    if command in installed:
                        raise ValueError(f"Duplicate selected command: {command}")
                    installed[command] = path
        publish(installed, bin_dir, data_dir / "packages")
    return installed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "profile",
        help="Named environment, or a selection identity with --native/--python",
    )
    parser.add_argument(
        "--prefix", type=Path, default=Path.home() / ".local/share/score-tools"
    )
    parser.add_argument("--catalog-root", type=Path, default=TOOLS_ROOT)
    parser.add_argument("--native", nargs="*", default=None)
    parser.add_argument("--python", nargs="*", default=None)
    args = parser.parse_args(argv)
    try:
        if args.native is None and args.python is None:
            selections = json.loads(
                (args.catalog_root / "environments.json").read_text()
            )
            selection = selections[args.profile]
            native, python = selection.get("native", []), selection.get("python", [])
        else:
            native, python = args.native or [], args.python or []
        result = provision(
            args.profile,
            native,
            python,
            bin_dir=args.prefix / "bin",
            data_dir=args.prefix / "data",
            root=args.catalog_root,
        )
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Provisioning failed: {exc}\n")
    print(json.dumps({name: str(path) for name, path in result.items()}, indent=2))
    return 0
