# ============================================================
# utils.py
# ============================================================
# Shared helper functions imported by all scraper files.
# ============================================================

import re


def parse_shorthand(text):
    """
    Converts abbreviated follower counts into plain integers.

    Examples:
        "12.4K"  ->  12400
        "3.2M"   ->  3200000
        "1.1B"   ->  1100000000
        "5,000"  ->  5000
    """
    if not text:
        return None

    text = text.strip().upper().replace(",", "")

    match = re.search(r'([\d.]+)\s*([KMB]?)', text)
    if not match:
        return None

    num    = float(match.group(1))
    suffix = match.group(2)

    multipliers = {
        "K": 1_000,
        "M": 1_000_000,
        "B": 1_000_000_000,
    }

    return int(num * multipliers.get(suffix, 1))