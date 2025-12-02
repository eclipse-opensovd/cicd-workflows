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
      pre-commit-version: "4.2"  # Optional, defaults to 4.2
      pre-commit-config-path: ""  # Optional, uses action's default config if not specified
      license-config-path: ""  # Optional, uses action's default config if not specified
```

#### Available Inputs

- `rust-nightly-version` (optional): Rust nightly version to use for Rust formatting in the format `YYYY-MM-DD`. Defaults to `2025-07-14`.
- `python-version` (optional): Python version to use for pre-commit environment. Defaults to `3.13`.
- `pre-commit-version` (optional): Version of pre-commit to install. Defaults to `4.2`.
- `pre-commit-config-path` (optional): Path to a custom `.pre-commit-config.yml` in your repository. If not provided, uses the action's default config.
- `license-config-path` (optional): Path to a custom `.licenserc.yml` in your repository. If not provided, uses the action's default config.

### Using Individual Actions

You can also use the individual actions directly in your workflows:

#### Pre-commit Checks Action

Runs pre-commit hooks with standardized configuration:

```yaml
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: eclipse-opensovd/cicd-workflows/pre-commit-action@main
        with:
          python-version: "3.13"  # Optional, defaults to 3.13
          pre-commit-version: "4.2"  # Optional, defaults to 4.2
          config-path: ""  # Optional, uses action's default config if not specified
```

## Actions in This Repository

### Pre-commit Action (`pre-commit-action/`)

Provides comprehensive code quality checks via uv and pre-commit.
All formatters **automatically fix issues** and **fail when changes are made**.

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
- **Apache SkyWalking Eyes**: Automatically adds or fixes license headers
- Runs twice for reliability:
  1. As a pre-commit hook (uses `license-eye` CLI, requires local installation)
  2. As a dedicated GitHub Action step (uses Docker, always available in CI)

**How Auto-fix Works:**
When a formatter makes changes to your code, the pre-commit hook fails, requiring you to review and commit the changes. This ensures:
- All code modifications are tracked in version control
- Developers can review formatting changes before committing
- CI pipelines fail if code is not properly formatted

**Inputs:**
- `python-version`: Python version for pre-commit environment (default: `3.13`)
- `pre-commit-version`: Version of pre-commit to install (default: `4.2`)
- `config-path`: Path to custom `.pre-commit-config.yml` (optional)
- `license-config-path`: Path to custom `.licenserc.yml` (optional)


## Running Checks Locally

### Using uv for Pre-commit Checks

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that can run Python scripts without needing to install dependencies globally.

#### In This Repository

To run pre-commit checks locally in this repository:

```bash
uv tool run pre-commit@4.2 run --all-files --config pre-commit-action/.pre-commit-config.yml
```

#### In Your Repository (Using This Action's Config)

You have two options to run the same checks locally that run in CI:

**Option 1: Using the `run_checks.py` script (One-off execution)**

```bash
# Run with the default 'main' branch config
uv run https://raw.githubusercontent.com/eclipse-opensovd/cicd-workflows/main/run_checks.py

# Or specify a different branch/tag/commit
uv run https://raw.githubusercontent.com/eclipse-opensovd/cicd-workflows/main/run_checks.py your-branch-name
```

This script will:
1. Download the shared pre-commit configuration from this repository
2. Download the shared license configuration (`.licenserc.yml`)
3. Set up the environment to run all checks (including license header validation)
4. Run all pre-commit checks against your code
5. Clean up temporary files automatically

**Option 2: Using pre-commit directly (Recommended for development)**

Create a `.pre-commit-config.yaml` file in your repository root:

```yaml
repos:
  - repo: local
    hooks:
      - id: shared-checks
        name: Shared pre-commit checks
        entry: uv run https://raw.githubusercontent.com/eclipse-opensovd/cicd-workflows/main/run_checks.py
        language: system
        pass_filenames: false
```

Then install and use pre-commit normally:

```bash
# Install pre-commit hooks (runs automatically on git commit)
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

**Custom Config**: If you've specified a custom `pre-commit-config-path` in your workflow, you can run pre-commit directly:
```bash
uv tool run pre-commit@4.2 run --all-files --config .pre-commit-config.yml
```

**Run Specific Hooks**: To run only the shared checks:
```bash
pre-commit run shared-checks --all-files
```

### Installing Required Tools

#### uv (Required)

[Install uv](https://docs.astral.sh/uv/getting-started/installation/) - Fast Python package manager and script runner.

#### Apache SkyWalking Eyes (Required for License Checks)

[Install SkyWalking Eyes](https://github.com/apache/skywalking-eyes#installation) - Required for local license header validation.

#### Rust Toolchain (Required for Rust Projects)

[Install Rust](https://www.rust-lang.org/tools/install) - Required if your project has a `Cargo.toml` file.
