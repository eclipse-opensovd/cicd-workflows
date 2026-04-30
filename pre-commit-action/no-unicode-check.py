#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0

import sys


def check_file(path):
    """Return a list of 1-indexed line numbers on which non-ASCII bytes are found.

    Returns None if the file cannot be read (error already printed to stderr).
    """
    line_numbers = []
    try:
        with open(path, "rb") as f:
            for line_number, line in enumerate(f, start=1):
                if any(byte > 127 for byte in line):
                    line_numbers.append(line_number)
    except OSError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return None
    return line_numbers


def main():
    if len(sys.argv) < 2:
        sys.exit(0)

    found_violations = False
    for path in sys.argv[1:]:
        line_numbers = check_file(path)
        if line_numbers is None:
            found_violations = True
            continue
        if line_numbers:
            found_violations = True
            for line_number in line_numbers:
                print(f"{path}:{line_number}: non-ASCII character found")

    sys.exit(1 if found_violations else 0)


if __name__ == "__main__":
    main()
