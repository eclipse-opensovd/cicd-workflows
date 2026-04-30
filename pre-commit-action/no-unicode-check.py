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

import argparse
import sys


def check_file(path, allowed_chars):
    """Return a list of (line_number, offending_chars) tuples for disallowed non-ASCII characters.

    Characters in *allowed_chars* are exempt from the check.
    Returns None if the file cannot be read (error already printed to stderr).
    """
    violations = []
    try:
        with open(path, "rb") as f:
            for line_number, raw_line in enumerate(f, start=1):
                # Fast path: skip lines with only ASCII bytes.
                if not any(byte > 127 for byte in raw_line):
                    continue
                # Decode to inspect individual characters.
                try:
                    text = raw_line.decode("utf-8")
                except UnicodeDecodeError:
                    # Non-UTF-8 bytes are always a violation.
                    violations.append((line_number, ["<non-UTF-8>"]))
                    continue
                bad = sorted(
                    {c for c in text if ord(c) > 127 and c not in allowed_chars}
                )
                if bad:
                    violations.append((line_number, bad))
    except OSError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return None
    return violations


def main():
    parser = argparse.ArgumentParser(
        description="Check files for disallowed non-ASCII characters.",
    )
    parser.add_argument(
        "--allowed-chars",
        default="",
        help="Comma-separated Unicode characters that are permitted (e.g. '\u00b5,\u00a7').",
    )
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    if not args.files:
        sys.exit(0)

    allowed_chars = {c.strip() for c in args.allowed_chars.split(",") if c.strip()}
    found_violations = False
    for path in args.files:
        violations = check_file(path, allowed_chars)
        if violations is None:
            found_violations = True
            continue
        if violations:
            found_violations = True
            for line_number, chars in violations:
                pretty = " ".join(
                    f"{c} (U+{ord(c):04X})" if c != "<non-UTF-8>" else c for c in chars
                )
                print(f"{path}:{line_number}: non-ASCII character(s) found: {pretty}")

    sys.exit(1 if found_violations else 0)


if __name__ == "__main__":
    main()
