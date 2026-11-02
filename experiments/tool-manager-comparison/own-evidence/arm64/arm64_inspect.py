#!/usr/bin/env python3
"""Verify prepared command provenance and ELF machine, not substrate fallback."""
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import sys

sys.path.insert(0, "/own-tools")
from score_tools.catalog import load_catalog_versions

prefix = Path(sys.argv[1])
output = Path(sys.argv[2])
expected = {
    "actionlint", "apm", "bazelisk", "buildifier", "opencode", "ruff",
    "shellcheck", "starpls", "uv", "uvx", "yamlfmt", "basedpyright",
    "basedpyright-langserver", "pre-commit", "pytest", "py.test",
}
native = {
    "actionlint", "apm", "bazelisk", "buildifier", "opencode", "ruff",
    "shellcheck", "starpls", "uv", "uvx", "yamlfmt",
}
assert platform.machine() == "aarch64"
assert os.getuid() == 1000


def inspect(path):
    with path.open("rb") as stream:
        header = stream.read(64)
        stream.seek(0)
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    result = {"path": str(path), "sha256": digest}
    if header.startswith(b"\x7fELF"):
        endian = "<" if header[5] == 1 else ">"
        machine = struct.unpack(endian + "H", header[18:20])[0]
        assert machine == 183, (str(path), machine)
        result.update({"format": "ELF", "machine": machine, "architecture": "AArch64"})
    elif header.startswith(b"#!"):
        result.update({"format": "script", "shebang": header.splitlines()[0].decode()})
    else:
        raise AssertionError(f"Unknown command format: {path}")
    return result


commands = {}
for name in sorted(expected):
    link = prefix / "bin" / name
    target = link.resolve(strict=True)
    assert link.is_symlink() and target.is_relative_to(prefix / "data/packages"), name
    commands[name] = {"exposed": str(link), **inspect(target)}
    if name in native:
        assert commands[name]["format"] == "ELF", name

interpreters = {}
for name in ("basedpyright", "pre-commit", "pytest"):
    target = Path(commands[name]["path"])
    interpreter = (target.parent / "python").resolve(strict=True)
    interpreters[name] = inspect(interpreter)
    assert interpreters[name]["format"] == "ELF"
node_paths = list((prefix / "data/packages").glob(
    "basedpyright-*/tools/basedpyright/lib/python*/site-packages/nodejs_wheel/bin/node"))
assert len(node_paths) == 1, node_paths
node = inspect(node_paths[0])
assert node["format"] == "ELF"
versions = load_catalog_versions()
output.write_text(json.dumps({
    "status": "passed", "machine": platform.machine(), "uid": os.getuid(),
    "prefix": str(prefix), "commands": commands,
    "owner_versions": {name: versions["pytest" if name == "py.test" else
                                     "basedpyright" if name == "basedpyright-langserver"
                                     else name] for name in sorted(expected)},
    "python_interpreters": interpreters, "bundled_node": node,
    "boundary": "Prepared commands and Python Node executable, not every shared object or substrate provider.",
}, indent=2) + "\n")
print(output)
