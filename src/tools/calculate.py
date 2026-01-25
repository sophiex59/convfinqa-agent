"""Calculate tool - performs safe arithmetic calculations."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class CalculateInput(BaseModel):
    """Input schema for calculate tool."""
    expression: str = Field(
        description="Mathematical expression to evaluate, e.g., '100 - 80' or '(50 - 40) / 40 * 100'"
    )


# Allowed names for safe eval
SAFE_MATH_NAMES = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
}


@tool(args_schema=CalculateInput)
def calculate(expression: str) -> str:
    """
    Perform a mathematical calculation.
    Use this for ALL arithmetic operations - do not do mental math.

    Args:
        expression: A mathematical expression using +, -, *, /, and parentheses.
                   Can also use abs(), round(), min(), max(), pow().
                   Examples: "100 - 80", "(150 - 100) / 100", "round(3.14159, 2)"

    Returns:
        The result of the calculation, or an error message.
    """
    # Clean the expression
    expr = str(expression).strip()

    # Remove any currency symbols or commas
    expr = expr.replace("$", "").replace(",", "")

    # Basic safety check - only allow safe characters
    allowed_chars = set("0123456789.+-*/()% abcdefghijklmnopqrstuvwxyz")
    if not all(c.lower() in allowed_chars for c in expr):
        return f"Error: Expression contains invalid characters: {expr}"

    try:
        # Use eval with restricted globals for safety
        result = eval(expr, {"__builtins__": {}}, SAFE_MATH_NAMES)

        # Round to 5 decimal places for consistency
        if isinstance(result, float):
            result = round(result, 5)

        return f"Result: {result}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error calculating '{expr}': {str(e)}"
