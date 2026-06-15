#!/usr/bin/env bash

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

set -euo pipefail

if [ ! -f Cargo.toml ]; then
    exit 0
fi

# Default: --all-features --all-targets -D warnings
# Override: pass any args to take full control (e.g. to omit --all-features):
#   args: ["--all-targets", "--", "-D", "warnings"]
if [ $# -gt 0 ]; then
    exec cargo clippy --locked "$@"
else
    exec cargo clippy --locked --all-features --all-targets -- -D warnings
fi
