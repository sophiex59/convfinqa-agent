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
    
    # 3. Handle word multipliers (million/billion)
    multiplier = 1
    if "billion" in s:
        multiplier = 1000  # Scaling up to millions (standard base unit)
        s = s.replace("billion", "").strip()
    elif "million" in s:
        multiplier = 1
        s = s.replace("million", "").strip()
    
    # 4. Attempt float conversion
    try:
        # Extract first number-like string if multiple words remain
        nums = re.findall(r"-?\d+\.?\d*", s)
        if not nums:
            return s
            
        val = float(nums[0]) * multiplier
        
        # If it was a percentage, convert to decimal (e.g., 14.2 -> 0.142)
        if is_pct:
            val = val / 100
            
        return round(val, 5)
    except (ValueError, IndexError):
        return s
