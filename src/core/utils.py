"""Common utilities for ConvFinQA Agent."""

import re
from typing import Union


def normalize_answer(answer: Union[float, str, int]) -> Union[float, str]:
    """
    Normalize a numeric answer for comparison or submission.

    Handles:
    - Stripping $, %, and ,.
    - Converting "million" and "billion" to numeric scales.
    - Handling percentage-to-decimal conversion.
    """
    if answer is None:
        return ""

    s = str(answer).strip().lower()

    # 1. Handle common symbols
    s = s.replace("$", "").replace(",", "")

    # 2. Handle percentage
    is_pct = "%" in s
    if is_pct:
        s = s.replace("%", "").strip()

    # 3. Handle accounting negatives (parentheses)
    # Check this AFTER stripping $ but BEFORE other operations for best results
    # Assumption: (100) -> -100
    is_negative = False
    if "(" in s and ")" in s:
        s = s.replace("(", "").replace(")", "").strip()
        is_negative = True

    # 4. Handle word multipliers (million/billion)
    # NOTE: We DO NOT scale the number here. We only strip the words.
    # The Agent is responsible for unit conversion if needed.
    if "billion" in s:
        s = s.replace("billion", "").strip()
    elif "million" in s:
        s = s.replace("million", "").strip()

    # 5. Attempt float conversion
    try:
        # Extract first number-like string if multiple words remain
        nums = re.findall(r"-?\d+\.?\d*", s)
        if not nums:
            return s

        val = float(nums[0])

        # If it was a percentage, convert to decimal (e.g., 14.2 -> 0.142)
        if is_pct:
            val = val / 100

        # Apply specific negative sign if parentheses were detected
        if is_negative:
            val = -abs(val)

        return round(val, 5)
    except (ValueError, IndexError):
        return s
