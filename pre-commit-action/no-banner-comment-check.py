#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0

# /// script
# dependencies = []
# ///

import argparse
import re
import sys

COMMENT_PREFIXES = ("///", "//!", "//", "/*", "*/", "#!", "#", "*")


def build_banner_pattern(banner_chars, min_length):
    """Return compiled regexes that together match banner-style comment lines.

    Two patterns are combined:
    1. A run of min_length+ fill chars anchored at the start or end of the
       stripped content (boundary = whitespace or string edge). Catches pure
       banners ('----------') and suffix-only banners ('===== title').
    2. A short fill-char prefix + label + long fill-char suffix, e.g.
       '-- label ------'. This catches the common '// -- section ----...'
       style even when the leading run is shorter than min_length.
    """
    escaped = re.escape(banner_chars)
    run = rf"[{escaped}]{{{min_length},}}"
    short_run = rf"[{escaped}]{{1,}}"
    anchored = re.compile(rf"(?:^{run}(?:\s|$)|(?:^|\s){run}$)")
    labeled = re.compile(rf"^{short_run}\s.+\s{run}$")
    return anchored, labeled


def strip_comment_content(line):
    """Strip leading whitespace and comment prefix; return None if not a comment."""
    stripped = line.lstrip()
    for prefix in COMMENT_PREFIXES:
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return None


def check_file(path, patterns, skip_lines=0):
    """Return list of (line_number, line_text) for banner lines found."""
    violations = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line_number, line in enumerate(f, start=1):
                if line_number <= skip_lines:
                    continue
                content = strip_comment_content(line)
                if content is None or not content:
                    continue
                if any(p.search(content) for p in patterns):
                    violations.append((line_number, line.rstrip()))
    except OSError as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        sys.exit(1)
    return violations


def main():
    parser = argparse.ArgumentParser(
        description="Check files for banner-style comments.",
    )
    parser.add_argument(
        "--banner-chars",
        default="=-#*/~_+",
        help=(
            "Literal characters considered 'banner fill'. These are placed "
            "inside a regex character class [chars], so pass the raw characters "
            "you want to match (e.g. '=-#*/~_+'). Escaping is handled internally. "
            "Default: =-#*/~_+"
        ),
    )
    parser.add_argument(
        "--min-length",
        type=int,
        default=5,
        help="Minimum consecutive fill characters to flag a line (default: 5).",
    )
    parser.add_argument(
        "--skip-lines",
        type=int,
        default=0,
        help=(
            "Number of lines to skip at the start of each file (e.g. to ignore "
            "license headers). Default: 0 (check all lines)."
        ),
    )
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()

    if not args.files:
        sys.exit(0)

    patterns = build_banner_pattern(args.banner_chars, args.min_length)
    found_violations = False

    for path in args.files:
        violations = check_file(path, patterns, skip_lines=args.skip_lines)
        if violations:
            found_violations = True
            for line_number, text in violations:
                print(f"{path}:{line_number}: banner comment: {text}")

    sys.exit(1 if found_violations else 0)


if __name__ == "__main__":
    main()
