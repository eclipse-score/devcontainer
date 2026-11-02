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
"""Download the small, checksum-verified aqua build-time bootstrap."""

from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path
import platform
import tarfile
import tomllib
import urllib.request


TOOLS_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = TOOLS_DIR.parent if TOOLS_DIR.name == "tools" else None
OWNER_DIR = (
    REPOSITORY_ROOT / "tools/owners/aqua"
    if REPOSITORY_ROOT is not None
    else Path("/tmp/score-aqua-owner")
)


def _platform_name() -> str:
    system = platform.system()
    if system == "Linux":
        os_name = "linux"
    elif system == "Darwin":
        os_name = "darwin"
    else:
        raise SystemExit(f"Unsupported Aqua bootstrap OS: {system}")
    machine = platform.machine().lower()
    if machine in {"aarch64", "arm64"}:
        cpu = "arm64"
    elif machine in {"x86_64", "amd64"}:
        cpu = "amd64"
    else:
        raise SystemExit(f"Unsupported Aqua bootstrap CPU: {machine}")
    return f"{os_name}/{cpu}"


def bootstrap(
    output_dir: Path, target_platform: str | None = None, owner_dir: Path = OWNER_DIR
) -> Path:
    manifest = tomllib.loads(
        (owner_dir / "aqua-bootstrap.toml").read_text(encoding="utf-8")
    )
    target_platform = target_platform or _platform_name()
    try:
        archive = manifest["archives"][target_platform]
    except KeyError as exc:
        raise SystemExit(f"No aqua bootstrap artifact for {target_platform}") from exc
    url = (
        "https://github.com/aquaproj/aqua/releases/download/v"
        f"{manifest['version']}/{archive['name']}"
    )
    with urllib.request.urlopen(url) as response:
        data = response.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != archive["sha256"]:
        raise SystemExit(
            f"aqua bootstrap checksum mismatch: expected {archive['sha256']}, got {digest}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    binary_path = output_dir / "aqua"
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as package:
        member = package.getmember("aqua")
        stream = package.extractfile(member)
        if stream is None:
            raise SystemExit(f"Aqua bootstrap archive has no executable: {url}")
        binary_path.write_bytes(stream.read())
    binary_path.chmod(0o755)
    return binary_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--platform")
    parser.add_argument("--owner-dir", type=Path, default=OWNER_DIR)
    args = parser.parse_args()
    print(bootstrap(args.output_dir, args.platform, args.owner_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
