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
``version`` field via its ``custom.regex`` manager, but it cannot compute
the new sha256 digests. This script reads the version from each lockfile,
fetches the corresponding GitHub release, and updates download URLs, archive
member paths and SHA256 digests for every platform.

Usage:
    python3 tools/internal/refresh_lockfile_digests.py [LOCKFILE ...]

With no arguments, refreshes all ``tools/lockfiles/*.lock.json`` files that
contain a ``binaries`` list. Exits non-zero if any lockfile cannot be
refreshed (e.g. the release or an expected asset is missing).
"""

import json
import os
import re
import sys
import urllib.request
from urllib.parse import urlsplit

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
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _parse_release_url(url):
    """Split a GitHub release download URL into its components.

    Layout: https://github.com/<owner>/<repo>/releases/download/<tag>/<asset>
    Returns ``(owner, repo, tag, asset)`` or ``None`` if the URL does not match.
    """
    parsed = urlsplit(url)
    parts = parsed.path.split("/")
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or parsed.query
        or parsed.fragment
        or len(parts) != 7
        or parts[3:5] != ["releases", "download"]
        or not all(parts[1:])
    ):
        return None
    return parts[1], parts[2], parts[5], parts[6]


def _release_digests(owner, repo, tag, token, cache):
    """Return ``{asset name: digest}`` for a release, fetching each one once."""
    key = (owner, repo, tag)
    if key not in cache:
        release = _api_get(
            f"{GITHUB_API}/repos/{owner}/{repo}/releases/tags/{tag}", token
        )
        cache[key] = {a["name"]: a.get("digest", "") for a in release.get("assets", [])}
    return cache[key]


def refresh_lockfile(path, token=None, cache=None):
    """Refresh one lockfile in place. Returns a list of changed binary names."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    cache = {} if cache is None else cache
    changed = []
    for tool_name, tool in data.items():
        if not isinstance(tool, dict) or "binaries" not in tool:
            continue
        version = tool.get("version")
        if not version or not tool["binaries"]:
            raise ValueError(f"{tool_name}: version and binaries are required")

        for binary in tool["binaries"]:
            url = binary.get("url", "")
            parsed = _parse_release_url(url)
            if parsed is None:
                raise ValueError(f"{tool_name}: unsupported release URL {url!r}")
            owner, repo, old_tag, old_asset = parsed

            # Projects publish either v-prefixed or bare release tags. The URL
            # still carries the old version after Renovate updates the pin;
            # use it to update versioned asset names and archive member paths.
            prefix = "v" if old_tag.startswith("v") else ""
            old_version = old_tag.removeprefix("v")
            tag = prefix + version
            asset = old_asset.replace(old_version, version)
            digests = _release_digests(owner, repo, tag, token, cache)
            if asset not in digests:
                raise ValueError(
                    f"{tool_name}: missing asset {asset!r} in {owner}/{repo} {tag}"
                )
            digest = digests[asset]
            match = re.fullmatch(r"sha256:([0-9a-fA-F]{64})", digest or "")
            if match is None:
                raise ValueError(
                    f"{tool_name}: no valid SHA256 digest for {asset!r} in {tag}"
                )

            updated = {
                **binary,
                "url": f"https://github.com/{owner}/{repo}/releases/download/{tag}/{asset}",
                "sha256": match[1].lower(),
            }
            for field in ("file", "dir"):
                if field in updated:
                    updated[field] = updated[field].replace(old_version, version)
            if updated != binary:
                binary.update(updated)
                changed.append(f"{tool_name}/{asset}")

    # Validate every platform before writing: an incomplete upstream release
    # must not leave a lockfile with a mixture of old and new artifacts.
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

    cache = {}
    failed = False
    for path in argv[1:]:
        print(f"Refreshing {path}")
        try:
            changed = refresh_lockfile(path, token, cache)
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
