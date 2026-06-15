<!--
SPDX-FileCopyrightText: 2026 Copyright (c) Contributors to the Eclipse Foundation

See the NOTICE file(s) distributed with this work for additional
information regarding copyright ownership.

This program and the accompanying materials are made available under the
terms of the Apache License Version 2.0 which is available at
https://www.apache.org/licenses/LICENSE-2.0

SPDX-License-Identifier: Apache-2.0
-->

# AI Agent Guidelines

Guidance for AI coding assistants working in this repository.

## Do Not Generate Banner Comments

Do not generate banner-style decorative comments such as repeated `=` or `-` lines.
They add noise and will be rejected by the `no-banner-comment-check` hook.

Prefer clear names, small modules, and well-structured functions instead.

## Code Style

### Python

- Line length: 100 characters
- Formatter: `ruff format`
- Linter: `ruff check` with rules from `shared-config/ruff.toml`

### Rust

- Formatter: `cargo fmt` with `shared-config/.rustfmt.toml`
- Linter: `cargo clippy --all-features --all-targets -- -D warnings`
- Max line width: 100 characters

### Shell

- Shell scripts must pass `shellcheck`

## License Headers (REUSE/SPDX)

Every source file must include SPDX license headers. For Markdown files like this one, use an HTML comment block.

Do not remove or alter SPDX headers added by `reuse-annotate`.

## Sharing With Consumer Repos

Consumer repositories may copy or adapt this file for their own agent guidance. There is no automated distribution mechanism yet; keep copies in sync manually or reference a pinned canonical version.
