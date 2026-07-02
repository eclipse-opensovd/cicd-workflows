<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0
-->

# Reusable GitHub Actions Workflows

This repository contains **reusable GitHub Actions workflows** and **composite actions** designed to standardize CI/CD processes across multiple repositories in the Eclipse OpenSOVD project.

## Features

- 🔍 **Comprehensive Code Quality Checks**: YAML, Python, Rust, and TOML formatting and linting
- 📝 **Automated License Headers**: Automatically adds and validates Apache 2.0 license headers
- 🚀 **Fast Execution**: Uses modern tools like `uv`, `ruff`, and `taplo` for speed
- 🔧 **Auto-fix with Validation**: Formatters fix issues automatically but fail when changes are made
- 🌍 **Works Everywhere**: Run the same checks locally and in CI/CD pipelines
- ⚙️ **Highly Configurable**: Use default configs or provide your own

## Using the Workflows in Your Repository

To use a reusable workflow, create a workflow file inside **your repository** (e.g., `.github/workflows/ci.yml`) and reference the appropriate workflow from this repository.

### Using the Reusable CI Checks Workflow

The `checks.yml` workflow provides standardized pre-commit checks and license header validation. Add the following to your `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  checks:
    uses: eclipse-opensovd/cicd-workflows/.github/workflows/checks.yml@main
    with:
      rust-nightly-version: "2025-07-14"  # Optional, defaults to 2025-07-14
      python-version: "3.13"  # Optional, defaults to 3.13
      pre-commit-config-path: ""  # Optional, uses action's default config if not specified
      copyright-text: ""  # Optional, defaults to "The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)"
      license: ""  # Optional, defaults to "Apache-2.0"
      reuse-template: ""  # Optional, defaults to "opensovd"
```

#### Available Inputs

- `rust-nightly-version` (optional): Rust nightly version to use for Rust formatting in the format `YYYY-MM-DD`. Defaults to `2025-07-14`.
- `python-version` (optional): Python version to use for pre-commit environment. Defaults to `3.13`.
- `pre-commit-config-path` (optional): Path to a custom `.pre-commit-config.yml` in your repository. If not provided, uses the action's default config.
- `copyright-text` (optional): Copyright holder text for `reuse annotate` (e.g. `"ACME Inc."`). Defaults to `"The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)"`.
- `license` (optional): SPDX license identifier for `reuse annotate` (e.g. `"MIT"`). Defaults to `"Apache-2.0"`.
- `reuse-template` (optional): Name of the Jinja2 template in `.reuse/templates/` (without `.jinja2` suffix). Consumer repos can provide their own template. Defaults to `"opensovd"`.
- `no-unicode-extensions` (optional): Comma-separated list of file extensions (e.g. `".py,.rs,.c"`) whose contents are checked for non-ASCII bytes.
  Any file with a matching extension that contains a byte > 127 causes the check to fail. Disabled by default (empty string).
- `allowed-unicode-chars` (optional): Comma-separated Unicode characters permitted in files checked by `no-unicode-extensions`
  (e.g. `"µ,§"`). Empty by default (all non-ASCII characters are rejected).

### Using Individual Actions

You can also use the individual actions directly in your workflows:

#### Pre-commit Checks Action

Runs pre-commit hooks with standardized configuration:

```yaml
jobs:
  pre-commit:
    runs-on: ubuntu-26.04
    steps:
      - name: Run checks
        # Or use a long SHA instead of a branch (recommended)
        uses: eclipse-opensovd/cicd-workflows/pre-commit-action@main

```

#### Rust Lint And Format Action

```yaml

# Make sure to copy this into you CI pipeline too, otherwise review comments cannot be posted.
permissions:
  contents: read
  pull-requests: write # Grants permission to post review comments

jobs:
  format_and_clippy_nightly_toolchain_pinned:
    concurrency:
      group: format_and_clippy_nightly_toolchain_pinned-${{ github.ref }}
    runs-on: ubuntu-26.04
    continue-on-error: false
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          submodules: false
      - name: Format and Clippy
        uses: eclipse-opensovd/cicd-workflows/.github/workflows/checks.yml@main
        with:
          toolchain: nightly-2025-07-14
          github-token: ${{ secrets.GITHUB_TOKEN }}
          fail-on-format-error: 'true'
          fail-on-clippy-error: 'true'
          clippy-deny-warnings: 'true'
```

## Actions in This Repository

### Pre-commit Action (`pre-commit-action/`)

Provides comprehensive code quality checks via uv and pre-commit.
All formatters **automatically fix issues** and **fail when changes are made**.
This action additionally verifies that the lints from [shared-lints](shared-lints/README.md)
are applied in the Cargo.toml

#### Checks Performed

**File Validation:**

- YAML syntax validation
- Merge conflict detection
- End-of-file fixer (ensures files end with a newline)
- Trailing whitespace removal
- Mixed line ending normalization

**Code Formatting:**

- **YAML**: Formatted with `yamlfmt` using basic formatter with retained line breaks
- **Python**: Formatted with `ruff format` (extremely fast Python formatter)
- **TOML**: Formatted and linted with `taplo`
- **Rust**: Formatted with `cargo fmt` (only if `Cargo.toml` exists)
  - Long line and overflow checks
  - Import order using `StdExternalCrate` grouping
  - Import granularity using `Crate` setting

**Linting:**

- **Python**: `ruff check` for linting and code quality

**License Headers (Auto-fix):**

- **FSFE REUSE tool**: Automatically adds and validates license headers per the [REUSE Specification](https://reuse.software/)
- `reuse lint` validates all files have proper SPDX headers
- `reuse annotate` auto-adds headers to new files with the current year

**Lint verification:**

- [check-cargo-lints](shared-lints/check_cargo_lints.py): checks that the Cargo.toml (workspace or package) has all lints specified according to [shared-lints.toml](shared-lints/shared-lints.toml)

**How Auto-fix Works:**

When a formatter makes changes to your code, the pre-commit hook fails, requiring you to review and commit the changes. This ensures:

- All code modifications are tracked in version control
- Developers can review formatting changes before committing
- CI pipelines fail if code is not properly formatted

**Inputs:**

- `python-version`: Python version for pre-commit environment (default: `3.13`)
- `config-path`: Path to custom `.pre-commit-config.yml` (optional)
- `copyright-text`: Copyright holder text for `reuse annotate` (default: `"The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)"`)
- `license`: SPDX license identifier for `reuse annotate` (default: `"Apache-2.0"`)
- `reuse-template`: Name of Jinja2 template in `.reuse/templates/` (default: `"opensovd"`)
- `no-unicode-extensions`: Comma-separated file extensions to check for non-ASCII characters (e.g. `".py,.rs,.c"`).
  Disabled by default (empty string). When enabled, any file with a matching extension containing a byte > 127 fails the check.
- `allowed-unicode-chars`: Comma-separated Unicode characters permitted in files checked by `no-unicode-extensions` (e.g. `"µ,§"`).
  Empty by default.

## Running Checks Locally

Run all pre-commit hooks on your repository using [prek](https://github.com/j178/prek):

```bash
prek run --all-files
```

Or without installing prek globally:

```bash
uv run prek run --all-files
```

### Installing Required Tools

#### prek (Required)

[Install prek](https://github.com/j178/prek) - Pre-commit hook runner. Install via `uv tool install prek` or `pip install prek`.

#### FSFE REUSE tool (Required for License Checks)

[Install reuse](https://reuse.readthedocs.io/en/stable/readme.html) - Required for local license header validation. Install via `pip install reuse`.

#### Rust Toolchain (Required for Rust Projects)

[Install Rust](https://www.rust-lang.org/tools/install) - Required if your project has a `Cargo.toml` file.
