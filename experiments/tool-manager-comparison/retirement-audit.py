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
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Record the actual retirement boundary without treating old evidence as callers.

This static audit establishes deletion invariants, not runtime correctness or an
engineering-hours estimate. The common M5 contract also requires behavior tests.
"""

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path


LEGACY_ENGINE = {
    "_cmd_install",
    "_cmd_install_python",
    "_place_binary",
    "_extract_member",
    "_extract_dir",
}
PRODUCTION_ROOTS = (
    "tools",
    ".devcontainer",
    "scripts",
    ".github",
    "src/s-core-devcontainer/.devcontainer",
)
SOURCE_SUFFIXES = {
    ".py",
    ".sh",
    ".bzl",
    ".bazel",
    ".json",
    ".json5",
    ".yml",
    ".yaml",
    ".toml",
    ".Dockerfile",
}
SOURCE_NAMES = {"BUILD", "Dockerfile", "run-tool"}


def inventory(repo):
    installer = repo / "tools/internal/devcontainer/install.py"
    source = installer.read_text() if installer.exists() else ""
    tree = ast.parse(source)
    functions = sorted(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    commands = sorted(
        {
            node.args[0].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_parser"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        }
    )
    old_names = sorted(
        {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and node.id in LEGACY_ENGINE
        }
    )
    references = []
    refresh = []
    experiment_dependencies = []
    old_module_references = []
    for directory in PRODUCTION_ROOTS:
        for path in sorted((repo / directory).rglob("*")):
            if not path.is_file() or not (
                path.suffix in SOURCE_SUFFIXES or path.name in SOURCE_NAMES
            ):
                continue
            if any(
                part
                in {
                    "__pycache__",
                    ".venv",
                    "out",
                    "node_modules",
                    "prepared-tools",
                    "nix-runtime",
                    ".features",
                }
                for part in path.parts
            ):
                continue
            text = path.read_text()
            relative = str(path.relative_to(repo))
            for number, line in enumerate(text.splitlines(), 1):
                if "internal/devcontainer/install.py" in line:
                    old_module_references.append(
                        {"path": relative, "line": number, "text": line.strip()}
                    )
                if "experiments/tool-manager-" in line:
                    experiment_dependencies.append(
                        {"path": relative, "line": number, "text": line.strip()}
                    )
                if re.search(
                    r"install-python|_cmd_install\b|_cmd_install_python\b|install\.py[\"']?\s+install(?:-python)?(?:\s|$)",
                    line,
                ):
                    references.append(
                        {"path": relative, "line": number, "text": line.strip()}
                    )
                if path.suffix in {".json5", ".yml", ".yaml"} and re.search(
                    r"refresh_|sync_|ALLOWED_COMMANDS|postUpgradeTasks", line
                ):
                    refresh.append(
                        {"path": relative, "line": number, "text": line.strip()}
                    )
    environments = json.loads((repo / "tools/environments.json").read_text())
    return {
        "repo": str(repo),
        "installer_present": installer.exists(),
        "installer_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "installer_executable": (
            installer.stat().st_mode & 0o111 == 0o111 if installer.exists() else None
        ),
        "old_module_reference_candidates": old_module_references,
        "installer_functions": functions,
        "installer_subcommands": commands,
        "legacy_definitions": sorted(LEGACY_ENGINE.intersection(functions)),
        "legacy_name_references_in_installer": old_names,
        "legacy_call_or_test_candidates": references,
        "update_configuration_candidates": refresh,
        "production_experiment_reference_candidates": experiment_dependencies,
        "environments": {
            name: {kind: members.get(kind, []) for kind in ("native", "python")}
            for name, members in environments.items()
        },
        "boundaries": [
            "Historical experiment/evidence references excluded from production caller search",
            "Remaining source/test candidates need review: a negative API test is not a live installer caller",
            "No claim that static absence demonstrates successful feature/host/image provisioning",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expect-retired", action="store_true")
    args = parser.parse_args()
    report = inventory(args.repo.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    if args.expect_retired:
        assert report["installer_executable"] is not False, (
            "Remaining installer is invoked directly by feature scripts"
        )
        assert not report["legacy_definitions"], report["legacy_definitions"]
        assert not report["legacy_name_references_in_installer"], report[
            "legacy_name_references_in_installer"
        ]
        assert not {"install", "install-python"}.intersection(
            report["installer_subcommands"]
        ), report["installer_subcommands"]
    print(
        json.dumps(
            {
                "repo": report["repo"],
                "legacy_definitions": report["legacy_definitions"],
                "installer_subcommands": report["installer_subcommands"],
                "review_candidates": len(report["legacy_call_or_test_candidates"]),
            }
        )
    )


if __name__ == "__main__":
    main()
