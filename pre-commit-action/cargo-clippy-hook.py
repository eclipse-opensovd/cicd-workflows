#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 Copyright (c) Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0

# Dependency specification for `uv run`. See: https://peps.python.org/pep-0723
# /// script
# dependencies = []
# ///

"""
Pre-commit hook: run cargo clippy with an optional toolchain override.

Usage in .pre-commit-config.yaml:

  - id: cargo-clippy
    args:
      - --toolchain=nightly-2025-07-14
      - --all-targets
      - --all-features
      - --locked
      - --
      - -D
      - warnings
"""

import argparse
import os
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--toolchain", default=None)
    args, remaining = parser.parse_known_args()

    cargo = "cargo"
    cmd = [cargo]
    if args.toolchain:
        cmd.append(f"+{args.toolchain}")
    cmd.append("clippy")
    cmd.extend(remaining)

    result = subprocess.run(cmd, env=os.environ)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
