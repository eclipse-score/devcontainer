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
"""Exercise prepared, disposable starpls installations under real network isolation.

See operations-evidence/README.md for fixture preparation. Never point --workspace
at an accepted candidate cache: this probe deliberately corrupts and removes tools.
The Nix container must own a fresh store, separate from the cache producer.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--mise", type=Path, required=True)
    parser.add_argument("--aqua", type=Path, required=True)
    parser.add_argument("--nix-container", required=True)
    parser.add_argument("--image", default="score-mise-m3:local-amd64")
    args = parser.parse_args()
    work = args.workspace.resolve()
    root = Path(__file__).resolve().parents[2]
    records = []
    report = {
        "scope": "Linux amd64; starpls 0.1.22; task-owned installations",
        "commands": records,
    }

    def run(label, argv, *, cwd=None, env=None, offline=False):
        command = list(map(str, argv))
        if offline:
            command = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--user",
                f"{os.getuid()}:{os.getgid()}",
                "--mount",
                f"type=bind,src={work},dst={work}",
                "--mount",
                f"type=bind,src={root},dst={root},readonly",
                "--mount",
                f"type=bind,src={args.mise},dst=/managers/mise,readonly",
                "--mount",
                f"type=bind,src={args.aqua},dst=/managers/aqua,readonly",
                "--workdir",
                str(cwd or work),
                "--env",
                f"HOME={work}/home",
                "--env",
                "PATH=/usr/bin:/bin",
                "--env",
                f"XDG_CACHE_HOME={work}/xdg-cache",
                *[
                    v
                    for key, value in (env or {}).items()
                    for v in ("--env", f"{key}={value}")
                ],
                "--entrypoint",
                "/usr/bin/timeout",
                args.image,
                "25",
                *command,
            ]
        result = subprocess.run(
            command,
            cwd=cwd,
            env={**os.environ, **(env or {})},
            text=True,
            capture_output=True,
            timeout=120,
        )
        records.append(
            {
                "label": label,
                "network_none": offline
                or command[:3] == ["docker", "exec", args.nix_container],
                "argv": command,
                "exit": result.returncode,
                "stdout": result.stdout[-5000:],
                "stderr": result.stderr[-5000:],
            }
        )
        (work / "operations-results.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        return result

    paths = {
        "mise": work
        / "mise/data/installs/github-withered-magic-starpls/0.1.22/starpls",
        "aqua": work
        / "aqua/root/pkgs/github_release/github.com/withered-magic/starpls/v0.1.22/starpls-linux-amd64/starpls-linux-amd64",
        "baseline": work / "baseline/bin/starpls",
    }
    mise_dir = work / "mise"
    mise_env = {
        f"MISE_{key}_DIR": str(mise_dir / value)
        for key, value in {
            "CONFIG": "config",
            "SYSTEM_CONFIG": "system",
            "CACHE": "cache",
            "DATA": "data",
            "STATE": "state",
        }.items()
    }
    mise_env.update(
        MISE_TRUSTED_CONFIG_PATHS=str(mise_dir), MISE_YES="1", MISE_HTTP_TIMEOUT="5s"
    )
    aqua_dir = work / "aqua"
    aqua_env = {
        "AQUA_ROOT_DIR": str(aqua_dir / "root"),
        "AQUA_POLICY_CONFIG": str(aqua_dir / "policy.yaml"),
    }
    commands = {
        "mise": (
            ["/managers/mise", "--locked", "-C", str(mise_dir), "install"],
            mise_dir,
            mise_env,
        ),
        "aqua": (["/managers/aqua", "install"], aqua_dir, aqua_env),
        "baseline": (
            [
                "python3",
                str(root / "tools/internal/devcontainer/install.py"),
                "install",
                "starpls",
                "--destination",
                str(work / "baseline/bin"),
            ],
            work,
            {},
        ),
    }
    revalidated = work / "mise-revalidated"
    paths["mise-revalidated"] = (
        revalidated / "data/installs/github-withered-magic-starpls/0.1.22/starpls"
    )
    revalidated_env = {
        key: value.replace(str(mise_dir), str(revalidated))
        for key, value in mise_env.items()
    }
    commands["mise-revalidated"] = (
        ["/managers/mise", "--locked", "-C", str(revalidated), "install"],
        revalidated,
        revalidated_env,
    )
    for name, binary in paths.items():
        golden = digest(binary)
        backup = work / name / "pristine-starpls"
        shutil.copy2(binary, backup)
        with binary.open("ab") as stream:
            stream.write(b"\nSCORE disposable corruption fixture\n")
        assert digest(binary) != golden
        version = run(f"{name}.corrupt-version", [binary, "version"], offline=True)
        assert version.returncode == 0 and "0.1.22" in version.stdout
        cmd, cwd, env = commands[name]
        ordinary = run(
            f"{name}.ordinary-install-corrupt", cmd, cwd=cwd, env=env, offline=True
        )
        report[name] = {
            "golden_sha256": golden,
            "corrupt_version_passes": True,
            "ordinary_install_exit": ordinary.returncode,
            "ordinary_install_restored": binary.exists() and digest(binary) == golden,
        }
        if name.startswith("mise"):
            forced = run(
                f"{name}.force-repair-offline",
                [*cmd, "--force"],
                cwd=cwd,
                env=env,
                offline=True,
            )
            report[name]["force_repair_exit"] = forced.returncode
            report[name]["force_repair_restored"] = (
                binary.exists() and digest(binary) == golden
            )
        binary.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, binary)
        # Remove the expanded package, retaining all manager download/metadata caches.
        if name == "baseline":
            binary.unlink()
        else:
            shutil.rmtree(binary.parent)
        recovered = run(f"{name}.recover-offline", cmd, cwd=cwd, env=env, offline=True)
        report[name]["recover_exit"] = recovered.returncode
        report[name]["recover_restored"] = binary.exists() and digest(binary) == golden
        binary.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, binary)

    # An explicit baseline file mirror is separate from its default download path.
    lock = json.loads((root / "tools/lockfiles/starpls.lock.json").read_text())
    for item in lock["starpls"]["binaries"]:
        if item["os"] == "linux" and item["cpu"] == "x86_64":
            item["url"] = (work / "baseline/pristine-starpls").as_uri()
    mirror = work / "baseline/local-mirror.lock.json"
    mirror.write_text(json.dumps(lock, indent=2) + "\n")
    with paths["baseline"].open("ab") as stream:
        stream.write(b"\nSCORE disposable corruption fixture\n")
    mirror_run = run(
        "baseline.explicit-file-mirror-repair",
        [
            *commands["baseline"][0],
            "--lockfile",
            str(mirror).removesuffix(".lock.json"),
        ],
        offline=True,
    )
    report["baseline"]["explicit_mirror_repair"] = (
        mirror_run.returncode == 0
        and digest(paths["baseline"]) == report["baseline"]["golden_sha256"]
    )
    assert report["baseline"]["explicit_mirror_repair"]

    # Record native selection and fixed exports separately: old files are not proof
    # of an active command, and a changed config cannot alter an existing shell PATH.
    mise_config = mise_dir / "mise.toml"
    original_mise = mise_config.read_text()
    run(
        "mise.selected-paths-before",
        ["/managers/mise", "-C", mise_dir, "env", "--paths"],
        cwd=mise_dir,
        env=mise_env,
        offline=True,
    )
    fixed = mise_dir / "export"
    fixed.mkdir(exist_ok=True)
    shutil.copy2(paths["mise"], fixed / "starpls")
    mise_config.write_text("[tools]\n")
    try:
        run(
            "mise.apply-empty",
            commands["mise"][0],
            cwd=mise_dir,
            env=mise_env,
            offline=True,
        )
        after = run(
            "mise.selected-paths-after",
            ["/managers/mise", "-C", mise_dir, "env", "--paths"],
            cwd=mise_dir,
            env=mise_env,
            offline=True,
        )
        report["mise"].update(
            empty_selection_has_starpls_path="github-withered-magic-starpls"
            in after.stdout,
            old_export_remains=(fixed / "starpls").exists(),
        )
        assert (
            after.returncode == 0
            and not report["mise"]["empty_selection_has_starpls_path"]
        )
    finally:
        mise_config.write_text(original_mise)

    aqua_config = aqua_dir / "aqua.yaml"
    original_aqua = aqua_config.read_text()
    run(
        "aqua.copy-before",
        ["/managers/aqua", "cp", "-o", aqua_dir / "export"],
        cwd=aqua_dir,
        env=aqua_env,
        offline=True,
    )
    aqua_config.write_text(original_aqua.split("packages:")[0] + "packages: []\n")
    try:
        run(
            "aqua.apply-empty",
            commands["aqua"][0],
            cwd=aqua_dir,
            env=aqua_env,
            offline=True,
        )
        run(
            "aqua.copy-empty-over-existing",
            ["/managers/aqua", "cp", "-o", aqua_dir / "export"],
            cwd=aqua_dir,
            env=aqua_env,
            offline=True,
        )
        which = run(
            "aqua.which-after",
            ["/managers/aqua", "which", "starpls"],
            cwd=aqua_dir,
            env=aqua_env,
            offline=True,
        )
        report["aqua"].update(
            empty_selection_which_exit=which.returncode,
            old_export_remains=(aqua_dir / "export/starpls").exists(),
        )
        assert which.returncode != 0 and report["aqua"]["old_export_remains"]
    finally:
        aqua_config.write_text(original_aqua)

    copied_tools = work / "baseline/tools"
    shutil.copytree(
        root / "tools",
        copied_tools,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", ".venv"),
    )
    environments = copied_tools / "environments.json"
    selections = json.loads(environments.read_text())
    selections["operations-probe"] = {"native": [], "python": [], "apt": []}
    environments.write_text(json.dumps(selections))
    empty = run(
        "baseline.apply-empty",
        [
            "python3",
            copied_tools / "internal/devcontainer/install.py",
            "environment",
            "operations-probe",
            "--destination",
            work / "baseline/bin",
        ],
        offline=True,
    )
    report["baseline"].update(
        empty_selection_exit=empty.returncode,
        old_export_remains=paths["baseline"].exists(),
    )
    assert empty.returncode == 0 and report["baseline"]["old_export_remains"]

    # This cache was exported by a different Nix store. The target store is fresh,
    # disposable and network-isolated; only this fixture's NAR signatures are waived.
    container = args.nix_container
    metadata = json.loads((work / "nix/package.json").read_text())
    package, executable = metadata["store"], metadata["executable"]
    nix = [
        "docker",
        "exec",
        container,
        "nix",
        "--extra-experimental-features",
        "nix-command flakes",
    ]
    inspect = run(
        "nix.network",
        ["docker", "inspect", "--format", "{{.HostConfig.NetworkMode}}", container],
    )
    assert inspect.stdout.strip() == "none"
    initial = run(
        "nix.package-absent", ["docker", "exec", container, "test", "!", "-e", package]
    )
    assert initial.returncode == 0
    imported = run(
        "nix.offline-import",
        [
            *nix,
            "copy",
            "--offline",
            "--no-check-sigs",
            "--from",
            "file:///probe/cache",
            package,
        ],
    )
    assert imported.returncode == 0
    golden = run(
        "nix.golden-hash", ["docker", "exec", container, "sha256sum", executable]
    ).stdout.split()[0]
    run(
        "nix.corrupt",
        [
            "docker",
            "exec",
            container,
            "sh",
            "-c",
            'chmod u+w "$1"; printf "\\nSCORE disposable corruption fixture\\n" >> "$1"',
            "sh",
            executable,
        ],
    )
    version = run(
        "nix.corrupt-version", ["docker", "exec", container, executable, "version"]
    )
    assert version.returncode == 0 and "0.1.22" in version.stdout
    verify = run("nix.verify-corrupt", [*nix, "store", "verify", "--no-trust", package])
    assert verify.returncode != 0
    repaired = run(
        "nix.repair-from-file-cache",
        [
            *nix,
            "store",
            "repair",
            "--option",
            "substitute",
            "true",
            "--option",
            "substituters",
            "file:///probe/cache",
            "--option",
            "require-sigs",
            "false",
            package,
        ],
    )
    assert repaired.returncode == 0
    final_hash = run(
        "nix.repaired-hash", ["docker", "exec", container, "sha256sum", executable]
    ).stdout.split()[0]
    assert final_hash == golden
    assert (
        run(
            "nix.verify-repaired", [*nix, "store", "verify", "--no-trust", package]
        ).returncode
        == 0
    )
    assert (
        run(
            "nix.profile-install",
            [
                *nix,
                "profile",
                "install",
                "--offline",
                "--profile",
                "/probe/profile",
                package,
            ],
        ).returncode
        == 0
    )
    assert (
        run(
            "nix.selected-before",
            ["docker", "exec", container, "/probe/profile/bin/starpls", "version"],
        ).returncode
        == 0
    )
    assert (
        run(
            "nix.profile-remove",
            [
                *nix,
                "profile",
                "remove",
                "--offline",
                "--profile",
                "/probe/profile",
                "--all",
            ],
        ).returncode
        == 0
    )
    removed = run(
        "nix.selected-after-absent",
        ["docker", "exec", container, "test", "!", "-e", "/probe/profile/bin/starpls"],
    )
    assert removed.returncode == 0
    report["nix"] = {
        "golden_sha256": golden,
        "explicit_cache_import": True,
        "corrupt_version_passes": True,
        "verification_detected": True,
        "repair_restored": final_hash == golden,
        "removed_from_profile": True,
    }
    (work / "operations-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "commands"}, indent=2
        )
    )


if __name__ == "__main__":
    main()
