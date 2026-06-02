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

# Dependency specification for `uv run`. See: https://peps.python.org/pep-0723
# /// script
# dependencies = ["pyyaml"]
# requires-python = ">=3.11"
# ///

from __future__ import annotations

import re
import sys
from pathlib import Path

import tomllib
import yaml

REQUIRED_HOOKS: list[dict] = [
    {
        "name": "check-yaml",
        "description": "YAML syntax validation",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v6.0.0",
        "hook_ids": ["check-yaml"],
    },
    {
        "name": "check-toml",
        "description": "TOML syntax validation",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v6.0.0",
        "hook_ids": ["check-toml"],
    },
    {
        "name": "check-json",
        "description": "JSON syntax validation",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v6.0.0",
        "hook_ids": ["check-json"],
    },
    {
        "name": "check-merge-conflict",
        "description": "merge conflict marker detection",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v6.0.0",
        "hook_ids": ["check-merge-conflict"],
    },
    {
        "name": "end-of-file-fixer",
        "description": "ensure files end with a newline",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v6.0.0",
        "hook_ids": ["end-of-file-fixer"],
    },
    {
        "name": "trailing-whitespace",
        "description": "trailing whitespace removal",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v6.0.0",
        "hook_ids": ["trailing-whitespace"],
    },
    {
        "name": "mixed-line-ending",
        "description": "consistent line endings",
        "repo": "https://github.com/pre-commit/pre-commit-hooks",
        "rev": "v6.0.0",
        "hook_ids": ["mixed-line-ending"],
    },
    {
        "name": "yamlfmt",
        "description": "YAML formatting",
        "repo": "https://github.com/google/yamlfmt",
        "rev": "v0.21.0",
        "hook_ids": ["yamlfmt"],
    },
    {
        "name": "markdownlint",
        "description": "markdown linting",
        "repo": "https://github.com/igorshubovych/markdownlint-cli",
        "rev": "v0.48.0",
        "hook_ids": ["markdownlint", "markdownlint-docker"],
    },
    {
        "name": "ruff-check",
        "description": "Python linting (ruff)",
        "repo": "https://github.com/astral-sh/ruff-pre-commit",
        "rev": "v0.15.12",
        "hook_ids": ["ruff-check", "ruff"],
    },
    {
        "name": "ruff-format",
        "description": "Python formatting (ruff)",
        "repo": "https://github.com/astral-sh/ruff-pre-commit",
        "rev": "v0.15.12",
        "hook_ids": ["ruff-format"],
    },
    {
        "name": "gitleaks",
        "description": "secret/credential detection",
        "repo": "https://github.com/gitleaks/gitleaks",
        "rev": "v8.30.1",
        "hook_ids": ["gitleaks"],
    },
    {
        "name": "shellcheck",
        "description": "shell script linting",
        "repo": "https://github.com/koalaman/shellcheck-precommit",
        "rev": "v0.11.0",
        "hook_ids": ["shellcheck"],
    },
    {
        "name": "conventional-pre-commit",
        "description": "conventional commit message enforcement",
        "repo": "https://github.com/compilerla/conventional-pre-commit",
        "rev": "v4.4.0",
        "hook_ids": ["conventional-pre-commit"],
    },
    {
        "name": "reuse",
        "description": "REUSE license header compliance",
        "repo": "https://github.com/eclipse-opensovd/cicd-workflows",
        "rev": None,
        "hook_ids": ["reuse", "reuse-annotate"],
    },
    {
        "name": "check-hooks",
        "description": "hook configuration enforcement",
        "repo": "https://github.com/eclipse-opensovd/cicd-workflows",
        "rev": None,
        "hook_ids": ["check-hooks", "check-minimum-hooks"],
    },
]

RUST_HOOKS: list[dict] = [
    {
        "name": "cargo-fmt",
        "description": "Rust formatting",
        "repo": "https://github.com/eclipse-opensovd/cicd-workflows",
        "rev": None,
        "hook_ids": ["cargo-fmt", "fmt"],
    },
    {
        "name": "clippy",
        "description": "Clippy linting",
        "repo": "https://github.com/eclipse-opensovd/cicd-workflows",
        "rev": None,
        "hook_ids": ["clippy", "cargo-clippy"],
    },
    {
        "name": "validate-cargo-lints",
        "description": "Cargo.toml lint configuration validation",
        "repo": "https://github.com/eclipse-opensovd/cicd-workflows",
        "rev": None,
        "hook_ids": ["validate-cargo-lints"],
    },
]

_SHARED_CONFIG = Path(__file__).parent.parent / "shared-config"

REQUIRED_CONFIGS: list[dict] = [
    {
        "path": ".yamlfmt",
        "description": "yamlfmt configuration",
        "canonical": _SHARED_CONFIG / ".yamlfmt",
        "rust_only": False,
        "check_mode": "yaml_superset",
    },
    {
        "path": ".markdownlint.yaml",
        "description": "markdownlint configuration",
        "canonical": _SHARED_CONFIG / ".markdownlint.yaml",
        "rust_only": False,
        "check_mode": "yaml_superset",
    },
    {
        "path": ".rustfmt.toml",
        "description": "rustfmt configuration",
        "canonical": _SHARED_CONFIG / ".rustfmt.toml",
        "rust_only": True,
        "check_mode": "toml_superset",
    },
    {
        "path": "ruff.toml",
        "description": "ruff configuration",
        "canonical": _SHARED_CONFIG / "ruff.toml",
        "rust_only": False,
        "check_mode": "toml_superset",
    },
]

REPO_LINE = re.compile(r"^\s*-\s*repo:\s*(.+)$")
REV_LINE = re.compile(r"^\s*rev:\s*(.+)$")
ID_LINE = re.compile(r"^\s*-?\s*id:\s*(.+)$")


def parse_config(text: str) -> list[dict]:
    repos: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        m = REPO_LINE.match(line)
        if m:
            current = {"repo": m.group(1).strip(), "rev": None, "hook_ids": []}
            repos.append(current)
            continue
        if current is None:
            continue
        m = REV_LINE.match(line)
        if m and current["rev"] is None:
            current["rev"] = m.group(1).strip()
            continue
        m = ID_LINE.match(line)
        if m:
            current["hook_ids"].append(m.group(1).strip().strip("'\""))
    return repos


def all_hook_ids(repos: list[dict]) -> set[str]:
    ids: set[str] = set()
    for r in repos:
        ids.update(r["hook_ids"])
    return ids


def find_repo_for_hook(repos: list[dict], hook_ids: list[str]) -> dict | None:
    for r in repos:
        if any(hid in r["hook_ids"] for hid in hook_ids):
            return r
    return None


def check_hooks(
    repos: list[dict],
    hook_list: list[dict],
    failures: list[str],
) -> None:
    configured_ids = all_hook_ids(repos)
    for hook in hook_list:
        if not any(hid in configured_ids for hid in hook["hook_ids"]):
            failures.append(f"Missing hook: {hook['name']} ({hook['description']})")
            continue

        repo_entry = find_repo_for_hook(repos, hook["hook_ids"])
        if repo_entry and repo_entry["repo"] != hook["repo"]:
            failures.append(
                f"Wrong repo for {hook['name']}: "
                f"expected {hook['repo']!r}, got {repo_entry['repo']!r}"
            )

        if hook["rev"] is not None and repo_entry:
            actual_rev = repo_entry.get("rev")
            if actual_rev != hook["rev"]:
                failures.append(
                    f"Wrong version for {hook['name']}: "
                    f"expected {hook['rev']!r}, got {actual_rev!r}"
                )


def _is_superset(canonical: dict, actual: dict, path: str = "") -> list[str]:
    """Return a list of violation messages where actual does not cover canonical."""
    issues: list[str] = []
    for key, expected in canonical.items():
        full_key = f"{path}.{key}" if path else str(key)
        if key not in actual:
            issues.append(f"missing key {full_key!r}")
        elif isinstance(expected, dict):
            if not isinstance(actual[key], dict):
                actual_type = type(actual[key]).__name__
                issues.append(f"key {full_key!r} must be a mapping, got {actual_type}")
            else:
                issues.extend(_is_superset(expected, actual[key], full_key))
        elif actual[key] != expected:
            issues.append(f"key {full_key!r}: expected {expected!r}, got {actual[key]!r}")
    return issues


def check_configs(failures: list[str], has_rust: bool) -> None:
    for cfg in REQUIRED_CONFIGS:
        if cfg["rust_only"] and not has_rust:
            continue
        canonical_path: Path = cfg["canonical"]
        if not canonical_path.exists():
            failures.append(f"Canonical config not found in cicd-workflows: {canonical_path}")
            continue

        p = Path(cfg["path"])
        if not p.exists():
            failures.append(f"Missing config file: {cfg['path']} ({cfg['description']})")
            continue

        check_mode = cfg.get("check_mode", "exact")

        if check_mode == "yaml_superset":
            canonical_data = yaml.safe_load(canonical_path.read_text()) or {}
            actual_data = yaml.safe_load(p.read_text()) or {}
            issues = _is_superset(canonical_data, actual_data)
            if issues:
                failures.append(
                    f"Config file {cfg['path']} is missing required settings:\n"
                    + "".join(f"  - {issue}\n" for issue in issues)
                )
        elif check_mode == "toml_superset":
            canonical_data = tomllib.loads(canonical_path.read_text())
            actual_data = tomllib.loads(p.read_text())
            issues = _is_superset(canonical_data, actual_data)
            if issues:
                failures.append(
                    f"Config file {cfg['path']} is missing required settings:\n"
                    + "".join(f"  - {issue}\n" for issue in issues)
                )
        else:
            canonical = canonical_path.read_text()
            actual = p.read_text()
            if actual != canonical:
                failures.append(
                    f"Config file {cfg['path']} does not match canonical content.\n"
                    "  Expected:\n"
                    + "".join(f"    {line}\n" for line in canonical.splitlines())
                    + "  Got:\n"
                    + "".join(f"    {line}\n" for line in actual.splitlines())
                )


def main() -> int:
    config_path = Path(".pre-commit-config.yaml")
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])

    if not config_path.exists():
        print(f"Error: {config_path} not found", file=sys.stderr)
        print(
            "Repositories must have a .pre-commit-config.yaml with all required hooks.",
            file=sys.stderr,
        )
        return 1

    text = config_path.read_text()
    repos = parse_config(text)
    failures: list[str] = []

    check_hooks(repos, REQUIRED_HOOKS, failures)

    has_rust = any(Path(".").rglob("Cargo.toml"))
    if has_rust:
        check_hooks(repos, RUST_HOOKS, failures)

    check_configs(failures, has_rust)

    total_configs = sum(1 for c in REQUIRED_CONFIGS if not c["rust_only"] or has_rust)

    total_hooks = len(REQUIRED_HOOKS) + (len(RUST_HOOKS) if has_rust else 0)

    if failures:
        print(f"[FAIL] {len(failures)} issue(s) found in hook configuration:")
        for f in failures:
            for line in f.splitlines():
                print(f"  {line}")
        print()
        print(
            "See https://github.com/eclipse-opensovd/cicd-workflows for the "
            "canonical configuration."
        )
        return 1

    print(f"[OK] All {total_hooks} required hooks are correctly configured in {config_path}")
    print(f"[OK] All {total_configs} required config files contain the required settings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
