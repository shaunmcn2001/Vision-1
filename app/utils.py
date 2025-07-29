"""
Shared helper functions for the parcel API.

The primary function here, `parse_user_input`, normalises whatever the
user typed into a `(region, lot, section, plan)` tuple.  It recognises both
Queensland and New South Wales formats:

* **QLD** – `3RP123456` (lot + plan, no section)
* **NSW** – `43/DP12345` (lot/plan) or `43/1/DP12345` (lot/section/plan)

An unknown or malformed input yields `(None, None, None, None)`.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# QLD lot/plan pattern e.g. 3RP123456, 12SP789, 101CP1234
LOTPLAN_RE = re.compile(r"^(\d+)([A-Z]{1,3}[0-9]+)$")


def parse_user_input(inp: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Normalise a raw input string into a `(region, lot, section, plan)` tuple."""
    inp = inp.strip().upper()
    if not inp:
        return None, None, None, None

    # NSW formats → "43/DP12345" or "43/1/DP12345"
    if "/" in inp:
        parts = [p.strip() for p in inp.split("/")]
        if len(parts) == 3:
            return "NSW", parts[0], parts[1], parts[2]          # lot / section / plan
        if len(parts) == 2:
            return "NSW", parts[0], None, parts[1]              # lot / plan
        return None, None, None, None

    # QLD format → "3RP123456"
    m = LOTPLAN_RE.match(inp)
    if m:
        return "QLD", m.group(1), None, m.group(2)

    return None, None, None, None
