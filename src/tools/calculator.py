"""Calculator tool for numerical operations."""

import re
from typing import Union


def calculate(expression: str) -> Union[float, str]:
    """
    Safely evaluate a mathematical expression.
    
    Supports: +, -, *, /, parentheses, and common functions.
    
    Args:
        expression: Mathematical expression as string, e.g., "156.2 - 143.1"
        
    Returns:
        Computed result as float, or error message as string.
        
    Examples:
        >>> calculate("156.2 - 143.1")
        13.1
        >>> calculate("100 * 0.25")
        25.0
        >>> calculate("(60.94 - 25.14) / 25.14")
        1.4240...
    """
    try:
        # Clean the expression
        expr = expression.strip()
        
        # Remove currency symbols and commas
        expr = re.sub(r'[\$,]', '', expr)
        
        # Handle percentages (convert 25% to 0.25)
        expr = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'(\1/100)', expr)
        
        # Only allow safe characters
        allowed = set('0123456789.+-*/() ')
        if not all(c in allowed for c in expr):
            return f"Error: Invalid characters in expression: {expression}"
        
        # Evaluate safely
        result = eval(expr, {"__builtins__": {}}, {})
        
        return round(float(result), 6)
        
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: Could not evaluate '{expression}': {e}"


def percent_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change from old to new value.
    
    Args:
        old_value: Original value
        new_value: New value
        
    Returns:
        Percentage change as decimal (0.25 = 25%)
    """
    if old_value == 0:
        return float('inf') if new_value > 0 else float('-inf')
    return (new_value - old_value) / old_value


def format_as_percent(value: float, decimals: int = 2) -> str:
    """Format a decimal as percentage string."""
    return f"{value * 100:.{decimals}f}%"


def format_currency(value: float, symbol: str = "$") -> str:
    """Format a number as currency."""
    if value >= 1_000_000:
        return f"{symbol}{value/1_000_000:.1f} million"
    elif value >= 1_000:
        return f"{symbol}{value/1_000:.1f}K"
    return f"{symbol}{value:.2f}"
