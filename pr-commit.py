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
# dependencies = ["pre-commit==4.2"]
# ///

import runpy
import sys
from pathlib import Path

sys.argv[0] = "run_checks.py"
runpy.run_path(Path(__file__).parent / "run_checks.py", run_name="__main__")
