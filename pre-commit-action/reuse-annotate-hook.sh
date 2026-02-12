#!/usr/bin/env bash

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0

# Pre-commit hook helper: ensure files have REUSE-compliant SPDX headers.
#
# For each file, determines the year to use:
#   1. File has SPDX-FileCopyrightText with a year -> keep that year
#   2. File has old "Copyright (c) YEAR ..." -> extract and preserve that year
#   3. File has no copyright at all -> use current year
#
# Then runs reuse annotate to add/update the header (including template text).
#
# Configurable via env vars (with defaults):
#   REUSE_COPYRIGHT  - copyright holder text
#   REUSE_LICENSE    - SPDX license identifier
#   REUSE_TEMPLATE   - name of .reuse/templates/<name>.jinja2

set -euo pipefail

COPYRIGHT="${REUSE_COPYRIGHT:-The Contributors to Eclipse OpenSOVD (see CONTRIBUTORS)}"
LICENSE="${REUSE_LICENSE:-Apache-2.0}"
TPL="${REUSE_TEMPLATE:-opensovd}"

TPL_FLAG=""
if [ -f ".reuse/templates/${TPL}.jinja2" ]; then
    TPL_FLAG="--template=${TPL}"
fi

for f in "$@"; do
    # Determine comment style and skip-flag per file type
    # --style and --skip-unrecognised are mutually exclusive in reuse
    STYLE_FLAG=""
    SKIP_FLAG="--skip-unrecognised"
    case "$f" in
        *.rs | *.kt | *.kts)
            STYLE_FLAG="--style=c"
            SKIP_FLAG=""
            ;;
        *.odx-*)
            STYLE_FLAG="--style=html"
            SKIP_FLAG=""
            ;;
    esac

    # Determine the year: preserve existing, or use current for new files
    EXISTING_YEAR=$(grep 'SPDX-FileCopyrightText' "$f" 2>/dev/null | grep -o '[0-9]\{4\}' | head -1 || true)
    if [ -n "$EXISTING_YEAR" ]; then
        YEAR="$EXISTING_YEAR"
    else
        OLD_YEAR=$(grep 'Copyright[[:space:]]*(c)' "$f" 2>/dev/null | grep -o '[0-9]\{4\}' | head -1 || true)
        if [ -n "$OLD_YEAR" ]; then
            YEAR="$OLD_YEAR"
        else
            YEAR="$(date +%Y)"
        fi
    fi

    # Remove any SPDX-FileCopyrightText lines with wrong copyright text so
    # reuse annotate doesn't just append a second copyright line.
    if grep -q 'SPDX-FileCopyrightText' "$f" 2>/dev/null; then
        if ! grep -q "SPDX-FileCopyrightText:.*${COPYRIGHT}" "$f" 2>/dev/null; then
            sed -i.bak '/SPDX-FileCopyrightText/d' "$f" && rm -f "$f.bak"
        fi
    fi

    # shellcheck disable=SC2086
    reuse annotate \
        --copyright="$COPYRIGHT" \
        --license="$LICENSE" \
        $TPL_FLAG $STYLE_FLAG $SKIP_FLAG \
        --merge-copyrights \
        --year="$YEAR" \
        "$f" || true
done
