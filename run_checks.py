# Copyright (c) 2025 The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
#
#!/usr/bin/env python3
# /// script
# dependencies = ["pre-commit==4.2"]
# ///

import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# Default to 'main' branch, but can be overridden via environment variable or argument
DEFAULT_BRANCH = "main"
BASE_URL = "https://raw.githubusercontent.com/eclipse-opensovd/cicd-workflows/{branch}/pre-commit-action"
CONFIG_URL_TEMPLATE = f"{BASE_URL}/.pre-commit-config.yml"
LICENSE_CONFIG_URL_TEMPLATE = f"{BASE_URL}/.licenserc.yml"


def main():
    branch = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BRANCH
    config_url = CONFIG_URL_TEMPLATE.format(branch=branch)
    license_config_url = LICENSE_CONFIG_URL_TEMPLATE.format(branch=branch)

    print(f"Downloading pre-commit config from: {config_url}")
    try:
        # Download pre-commit config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            with urllib.request.urlopen(config_url) as response:
                f.write(response.read().decode())
            config_path = f.name

        # Download license config
        print(f"Downloading license config from: {license_config_url}")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            with urllib.request.urlopen(license_config_url) as response:
                f.write(response.read().decode())
            license_config_path = f.name

        print("Running pre-commit checks...")
        # Set LICENSE_EYE_CONFIG so the license-eye hook knows where to find the config
        env = os.environ.copy()
        env["LICENSE_EYE_CONFIG"] = license_config_path

        result = subprocess.run(
            ["pre-commit", "run", "--all-files", "--config", config_path],
            env=env,
            check=False,
        )

        # Clean up temp files
        Path(config_path).unlink(missing_ok=True)
        Path(license_config_path).unlink(missing_ok=True)
        sys.exit(result.returncode)
    except urllib.error.HTTPError as e:
        print(f"Error downloading config: {e}", file=sys.stderr)
        print(
            f"Make sure the branch '{branch}' exists in the repository.",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
