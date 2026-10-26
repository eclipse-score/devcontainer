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
"""Refresh URLs and sha256 digests in tool lockfiles after a version bump.

Intended to run as a Renovate ``postUpgradeTask``: Renovate rewrites the
``version`` field (and the version embedded in each binary URL) via its
``custom.regex`` manager, but it cannot compute the new sha256 digests. This
script reads the (possibly new) version from each lockfile, fetches the
corresponding GitHub release, and rewrites every binary's ``url`` and
``sha256`` from the release's asset list.

Usage:
    python3 tools/internal/refresh_lockfile_digests.py [LOCKFILE ...]

With no arguments, refreshes all ``tools/lockfiles/*.lock.json`` files that
contain a ``binaries`` list. Exits non-zero if any lockfile cannot be
refreshed (e.g. the release or an expected asset is missing).
"""

import json
import os
import sys
import urllib.request

GITHUB_API = "https://api.github.com"


def _api_get(url, token=None):
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "score-devcontainer-lockfile-refresh",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def _asset_name(url):
    """Extract the asset filename from a GitHub release download URL."""
    return url.rsplit("/", 1)[-1]


def refresh_lockfile(path, token=None):
    """Refresh one lockfile in place. Returns a list of changed binary names."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    changed = []
    for tool_name, tool in data.items():
        if not isinstance(tool, dict) or "binaries" not in tool:
            continue
        version = tool.get("version")
        if not version:
            continue

        # Derive the GitHub repo from the first binary URL:
        #   https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>
        first_url = tool["binaries"][0].get("url", "")
        parts = first_url.split("/")
        if len(parts) < 9 or parts[2] != "github.com" or parts[5] != "releases":
            print(
                f"  ! {tool_name}: cannot derive repo from {first_url!r}",
                file=sys.stderr,
            )
            continue
        owner, repo = parts[3], parts[4]

        # Release tags are not uniformly prefixed: most projects publish
        # `v1.27.0`, while the astral-sh ones (uv, ruff) publish a bare
        # `0.13.5`. Reuse the prefix the pinned URL already encodes; assuming
        # `v` here would rewrite those tools to a nonexistent tag.
        tag = ("v" if parts[7].startswith("v") else "") + version

        release = _api_get(
            f"{GITHUB_API}/repos/{owner}/{repo}/releases/tags/{tag}", token
        )
        digests = {a["name"]: a.get("digest", "") for a in release.get("assets", [])}

        for binary in tool["binaries"]:
            asset = _asset_name(binary.get("url", ""))
            digest = digests.get(asset)
            if not digest:
                print(
                    f"  ! {tool_name}: no digest for asset {asset!r} in v{version}",
                    file=sys.stderr,
                )
                continue
            sha = digest.split(":", 1)[1] if digest.startswith("sha256:") else digest
            # Rebuild the URL from the version so the file is consistent
            # whether or not Renovate already updated the URL.
            new_url = (
                f"https://github.com/{owner}/{repo}/releases/download/{tag}/{asset}"
            )
            if binary.get("sha256") != sha or binary.get("url") != new_url:
                binary["url"] = new_url
                binary["sha256"] = sha
                changed.append(f"{tool_name}/{asset}")

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    return changed


def main(argv):
    token = os.environ.get("RENOVATE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not argv[1:]:
        lockdir = os.path.join(os.path.dirname(__file__), "..", "lockfiles")
        lockdir = os.path.abspath(lockdir)
        argv = [argv[0]] + [
            os.path.join(lockdir, name)
            for name in sorted(os.listdir(lockdir))
            if name.endswith(".lock.json")
        ]

    failed = False
    for path in argv[1:]:
        print(f"Refreshing {path}")
        try:
            changed = refresh_lockfile(path, token)
        except Exception as exc:
            print(f"  ! failed: {exc}", file=sys.stderr)
            failed = True
            continue
        if changed:
            for c in changed:
                print(f"  ~ {c}")
        else:
            print("  = up to date")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
