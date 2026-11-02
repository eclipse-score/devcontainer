#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
"""Native host and container provisioning entrypoint."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from score_tools.provision import main

if __name__ == "__main__":
    raise SystemExit(main())
