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

# /// script
# dependencies = ["pre-commit==4.2", "PyYAML>=6"]
# ///

import argparse
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

DEFAULT_BRANCH = "main"
REPO_BASE_URL = (
    "https://raw.githubusercontent.com/eclipse-opensovd/cicd-workflows/{branch}"
)
CONFIG_URL_TEMPLATE = f"{REPO_BASE_URL}/pre-commit-action/.pre-commit-config.yml"
TEMPLATE_URL_TEMPLATE = f"{REPO_BASE_URL}/.reuse/templates/{{template}}.jinja2"
LICENSE_URL_TEMPLATE = f"{REPO_BASE_URL}/LICENSES/{{license}}.txt"
REUSE_TOML_URL_TEMPLATE = f"{REPO_BASE_URL}/REUSE.toml"
STYLES_URL_TEMPLATE = f"{REPO_BASE_URL}/.reuse/styles.toml"
CLIPPY_LINTS_URL_TEMPLATE = f"{REPO_BASE_URL}/shared-lints/shared-lints.toml"
CLIPPY_LINTS_CHECK_SCRIPT_URL_TEMPLATE = (
    f"{REPO_BASE_URL}/shared-lints/check_cargo_lints.py"
)


DEFAULT_LICENSE = "Apache-2.0"
DEFAULT_TEMPLATE = "opensovd"


def extract_reuse_args_from_config(config_path):
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except Exception:
        return DEFAULT_LICENSE, DEFAULT_TEMPLATE

    for repo in config.get("repos", []):
        for hook in repo.get("hooks", []):
            if hook.get("id") == "reuse-annotate":
                args = hook.get("args", [])
                license_id = DEFAULT_LICENSE
                template = DEFAULT_TEMPLATE
                for arg in args:
                    if arg.startswith("--license="):
                        license_id = arg.split("=", 1)[1]
                    elif arg.startswith("--template="):
                        template = arg.split("=", 1)[1]
                return license_id, template

    return DEFAULT_LICENSE, DEFAULT_TEMPLATE


def download_if_missing(local_path, url, description):
    local_path = Path(local_path)
    if local_path.exists():
        return None

    print(f"Downloading {description} from: {url}")

    created_dirs = []
    check = local_path.parent
    while check != Path("."):
        if not check.exists():
            created_dirs.append(check)
        check = check.parent

    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with urllib.request.urlopen(url) as response:
            local_path.write_text(response.read().decode())
    except urllib.error.HTTPError:
        print(
            f"Warning: Could not download {description} from {url}",
            file=sys.stderr,
        )
        return None

    return {"file": local_path, "dirs": sorted(created_dirs)}


def cleanup_downloads(cleanup_list):
    for cleanup_info in cleanup_list:
        if cleanup_info is None:
            continue
        cleanup_info["file"].unlink(missing_ok=True)
        for d in reversed(cleanup_info["dirs"]):
            try:
                d.rmdir()
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Run pre-commit checks with REUSE license header support"
    )
    parser.add_argument(
        "branch",
        nargs="?",
        default=DEFAULT_BRANCH,
        help="Git branch to use for downloading configs (default: main)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to a local .pre-commit-config.yml (skips downloading from remote)",
    )

    args = parser.parse_args()
    branch = args.branch
    cleanup_list = []

    try:
        config_path = args.config
        if config_path is None:
            config_url = CONFIG_URL_TEMPLATE.format(branch=branch)
            print(f"Downloading pre-commit config from: {config_url}")
            config_tmp = Path(".pre-commit-config-remote.yml")
            with urllib.request.urlopen(config_url) as response:
                config_tmp.write_text(response.read().decode())
            cleanup_list.append({"file": config_tmp, "dirs": []})
            config_path = str(config_tmp)

        license_id, template = extract_reuse_args_from_config(config_path)

        cleanup_list.append(
            download_if_missing(
                "REUSE.toml",
                REUSE_TOML_URL_TEMPLATE.format(branch=branch),
                "REUSE.toml",
            )
        )
        cleanup_list.append(
            download_if_missing(
                f".reuse/templates/{template}.jinja2",
                TEMPLATE_URL_TEMPLATE.format(branch=branch, template=template),
                f"reuse template '{template}'",
            )
        )
        cleanup_list.append(
            download_if_missing(
                f"LICENSES/{license_id}.txt",
                LICENSE_URL_TEMPLATE.format(branch=branch, license=license_id),
                f"license text '{license_id}'",
            )
        )
        cleanup_list.append(
            download_if_missing(
                ".reuse/styles.toml",
                STYLES_URL_TEMPLATE.format(branch=branch),
                "reuse comment styles config",
            )
        )
        cleanup_list.append(
            download_if_missing(
                "shared-lints/shared-lints.toml",
                CLIPPY_LINTS_URL_TEMPLATE.format(branch=branch),
                "Clippy lints config",
            )
        )
        cleanup_list.append(
            download_if_missing(
                "shared-lints/check_cargo_lints.py",
                CLIPPY_LINTS_CHECK_SCRIPT_URL_TEMPLATE.format(branch=branch),
                "Clippy lints check script",
            )
        )

        print("Running pre-commit checks...")
        result = subprocess.run(
            ["pre-commit", "run", "--all-files", "--config", config_path],
            check=False,
        )
        sys.exit(result.returncode)
    except urllib.error.HTTPError as e:
        print(f"Error downloading config: {e}", file=sys.stderr)
        print(
            f"Make sure the branch '{branch}' exists in the repository.",
            file=sys.stderr,
        )
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        print(
            "Could not reach GitHub. Please check your internet connection and try again.",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cleanup_downloads(cleanup_list)


if __name__ == "__main__":
    main()
