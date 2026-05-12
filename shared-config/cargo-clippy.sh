#!/usr/bin/env bash

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2026 The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0

set -euo pipefail

if [ ! -f Cargo.toml ]; then
    exit 0
fi

if [ $# -gt 0 ]; then
    exec cargo clippy --locked "$@"
else
    exec cargo clippy --locked --all-targets -- -D warnings
fi
