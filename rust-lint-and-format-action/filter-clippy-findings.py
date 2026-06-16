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

"""Filter cargo clippy --message-format=json findings to lines changed in a git diff.

Reads clippy JSON lines from stdin, parses a unified diff to build a set of
changed (file, line) pairs, and outputs only findings whose primary span
falls within those changed lines.

When no diff file is given all findings are passed through unchanged.

Usage:
    cargo clippy --message-format=json 2>&1 | \\
        python3 filter-clippy-findings.py [--diff DIFF_FILE] [--output OUTPUT_FILE]

Outputs:
    - Human-readable rendered diagnostics to stdout (for terminal / step log)
    - GitHub Actions warning annotations to stdout (::warning file=...)
    - Markdown comment body to --output file (when specified)
    - Exit code 1 when any findings remain after filtering, 0 otherwise
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_diff_changed_lines(diff_text: str) -> dict[str, set[int]]:
    """Return a mapping of file path -> set of added/changed line numbers.

    Parses unified diff hunks (@@ -old +new,count @@) and records every
    new-side line number that was added or unchanged-context for the new file.
    We only care about lines present in the new version (i.e. lines the author
    touched), so we track lines from the '+' side of each hunk.
    """
    changed: dict[str, set[int]] = {}
    current_file: str | None = None
    new_line = 0

    for raw in diff_text.splitlines():
        # +++ b/src/foo.rs  -> strip the b/ prefix git adds
        if raw.startswith("+++ "):
            path = raw[4:]
            if path.startswith("b/"):
                path = path[2:]
            if path != "/dev/null":
                current_file = path
                changed.setdefault(current_file, set())
            else:
                current_file = None
            continue

        if current_file is None:
            continue

        # @@ -old_start,old_count +new_start,new_count @@
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", raw)
        if m:
            new_line = int(m.group(1))
            continue

        if raw.startswith("-"):
            # removed line - does not exist in new file, skip
            continue
        if raw.startswith("+"):
            changed[current_file].add(new_line)
            new_line += 1
        else:
            # context line - exists in both, advance new pointer
            new_line += 1

    return changed


def parse_clippy_json(lines: list[str]) -> list[dict]:
    """Parse cargo --message-format=json lines and return compiler-message entries."""
    findings = []
    for line in lines:
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("reason") != "compiler-message":
            continue
        msg = obj.get("message", {})
        # Skip bare notes/help without a lint code (e.g. "aborting due to N warnings")
        if not msg.get("code") and msg.get("level") not in ("warning", "error"):
            continue
        findings.append(msg)
    return findings


def primary_span(msg: dict) -> dict | None:
    """Return the primary span of a diagnostic, or None."""
    for span in msg.get("spans", []):
        if span.get("is_primary"):
            return span
    # Fall back to first span if none marked primary
    spans = msg.get("spans", [])
    return spans[0] if spans else None


def finding_in_diff(msg: dict, changed: dict[str, set[int]]) -> bool:
    """Return True if the primary span of msg touches a changed line."""
    span = primary_span(msg)
    if span is None:
        return False
    file_name = span.get("file_name", "")
    line_start = span.get("line_start", 0)
    line_end = span.get("line_end", line_start)

    file_lines = changed.get(file_name)
    if file_lines is None:
        # Try stripping a leading src/ prefix mismatch - some workspaces
        # emit relative paths differently in the diff vs clippy output.
        for diff_path, diff_lines in changed.items():
            if file_name.endswith(diff_path) or diff_path.endswith(file_name):
                file_lines = diff_lines
                break

    if file_lines is None:
        return False

    return any(ln in file_lines for ln in range(line_start, line_end + 1))


def render_findings(findings: list[dict]) -> str:
    """Return human-readable rendered output for the given findings."""
    parts = []
    for msg in findings:
        rendered = msg.get("rendered")
        if rendered:
            parts.append(rendered.rstrip())
    return "\n".join(parts)


def github_annotations(findings: list[dict]) -> list[str]:
    """Return GitHub Actions workflow command strings for each finding."""
    annotations = []
    for msg in findings:
        span = primary_span(msg)
        if span is None:
            continue
        level = msg.get("level", "warning")
        ann_level = "error" if level == "error" else "warning"
        file_name = span.get("file_name", "")
        line = span.get("line_start", 1)
        col = span.get("column_start", 1)
        end_line = span.get("line_end", line)
        end_col = span.get("column_end", col)
        title = msg.get("message", "clippy finding").replace("\n", " ")
        annotations.append(
            f"::{ann_level} file={file_name},line={line},endLine={end_line},"
            f"col={col},endColumn={end_col}::{title}"
        )
    return annotations


def build_comment_body(
    findings: list[dict],
    toolchain: str,
    run_url: str,
    diff_filtered: bool,
) -> str:
    """Build the markdown PR comment body."""
    marker = "<!-- nightly-clippy-report -->"
    disclaimer = (
        "These findings come from the nightly Rust compiler and are informational only. "
        "They do not block merging and may be unrelated to the changes introduced by this PR."
    )
    rendered = render_findings(findings)
    scope_note = " (filtered to lines changed in this PR)" if diff_filtered else ""
    lines = [
        marker,
        f"### Nightly Clippy Report ({toolchain}){scope_note}",
        "",
        f"> {disclaimer}",
        "",
        "**Status: Findings detected**",
        "",
        "```",
        rendered,
        "```",
        "",
        f"[Full build log]({run_url})",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--diff",
        metavar="FILE",
        help="Path to unified diff file (git diff output). When omitted all findings are reported.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write markdown PR comment body to this file.",
    )
    parser.add_argument(
        "--toolchain",
        default="nightly",
        help="Toolchain label shown in the PR comment header.",
    )
    parser.add_argument(
        "--run-url",
        default="",
        help="GitHub Actions run URL for the 'Full build log' link.",
    )
    args = parser.parse_args()

    raw_lines = sys.stdin.readlines()
    print(f"::debug::filter: read {len(raw_lines)} raw lines from stdin", file=sys.stderr)
    all_findings = parse_clippy_json(raw_lines)

    print(f"::debug::filter: parsed {len(all_findings)} findings from clippy JSON", file=sys.stderr)
    for f in all_findings:
        span = primary_span(f)
        loc = f"{span['file_name']}:{span['line_start']}" if span else "<no span>"
        code = f.get("code", {})
        code_str = code.get("code", "<none>") if isinstance(code, dict) else str(code)
        print(
            f"::debug::filter: finding level={f.get('level')} code={code_str} at {loc}",
            file=sys.stderr,
        )

    diff_filtered = False
    if args.diff:
        diff_text = Path(args.diff).read_text(errors="replace")
        changed = parse_diff_changed_lines(diff_text)
        print(f"::debug::filter: diff has {len(changed)} changed files", file=sys.stderr)
        for path, lines in changed.items():
            sorted_lines = sorted(lines)
            print(f"::debug::filter: diff file={path} lines={sorted_lines}", file=sys.stderr)
        if changed:
            pre_count = len(all_findings)
            all_findings = [f for f in all_findings if finding_in_diff(f, changed)]
            print(
                f"::debug::filter: {pre_count} -> {len(all_findings)} after diff filter",
                file=sys.stderr,
            )
            diff_filtered = True

    rendered = render_findings(all_findings)
    if rendered:
        print(rendered)

    for ann in github_annotations(all_findings):
        print(ann)

    if args.output and all_findings:
        body = build_comment_body(all_findings, args.toolchain, args.run_url, diff_filtered)
        Path(args.output).write_text(body)

    return 1 if all_findings else 0


if __name__ == "__main__":
    sys.exit(main())
