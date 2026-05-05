#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0

"""Check source files for banner-style comments and fail if any are found.

A banner comment is a line consisting almost entirely of repeated decorative
characters (e.g. ``=``, ``-``, ``#``, ``*``, ``/``, ``~``) that are used as
visual separators in source code.  Examples of lines that would be rejected::

    # ============================================================
    // ----------------------------------------------------------
    /* ********************************************************** */
    ################################
    // ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The check looks at each line after stripping leading/trailing whitespace and
any leading comment characters (``#``, ``/``, ``*``).  If the remaining
content is made up of at least *min_length* repetitions of a single
decorative character (from the configurable set), the line is flagged.
"""

import argparse
import re
import sys

# Characters that are considered "banner fill" characters.
DEFAULT_BANNER_CHARS = r"=\-#\*/~_+"

# Minimum number of repeated fill characters to classify a line as a banner.
DEFAULT_MIN_LENGTH = 5

# Regex that matches lines that are banners:
#   - optional leading whitespace
#   - optional comment prefix characters (#, /, *)
#   - optional whitespace
#   - a run of >= MIN_LENGTH identical fill characters
#   - optional trailing whitespace / comment close (e.g. */ or #)
_BANNER_RE_TEMPLATE = (
    r"^\s*[#/*]*\s*(?P<fill>[{chars}])\s*(?P=fill){{{min_len},}}\s*[#/*]*\s*$"
)


def build_pattern(banner_chars: str, min_length: int) -> re.Pattern:
    return re.compile(_BANNER_RE_TEMPLATE.format(chars=banner_chars, min_len=min_length - 1))


def check_file(path: str, pattern: re.Pattern) -> list[tuple[int, str]]:
    """Return a list of (line_number, line_text) tuples for banner lines.

    Returns an empty list when the file is clean.
    Returns None if the file cannot be read (error already printed to stderr).
    """
    violations = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line_number, line in enumerate(f, start=1):
                stripped = line.rstrip("\n")
                if pattern.match(stripped):
                    violations.append((line_number, stripped.strip()))
    except OSError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return None
    return violations


def main():
    parser = argparse.ArgumentParser(
        description="Check files for banner-style comments.",
    )
    parser.add_argument(
        "--banner-chars",
        default=DEFAULT_BANNER_CHARS,
        help=(
            "Character class (regex) of fill characters that define a banner "
            f"(default: '{DEFAULT_BANNER_CHARS}')."
        ),
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=DEFAULT_MIN_LENGTH,
        help=(
            "Minimum number of consecutive fill characters to flag a line "
            f"(default: {DEFAULT_MIN_LENGTH})."
        ),
    )
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    if not args.files:
        sys.exit(0)

    pattern = build_pattern(args.banner_chars, args.min_length)

    found_violations = False
    for path in args.files:
        violations = check_file(path, pattern)
        if violations is None:
            found_violations = True
            continue
        for line_number, line_text in violations:
            found_violations = True
            print(f"{path}:{line_number}: banner-style comment found: {line_text!r}")

    sys.exit(1 if found_violations else 0)


if __name__ == "__main__":
    main()
