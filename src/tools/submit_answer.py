"""Submit answer tool - finalizes the agent's response."""

from typing import Literal, Union

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class SubmitInput(BaseModel):
    """Input schema for submit_answer tool."""
    value: Union[float, str] = Field(description="The answer value")
    format: Literal["number", "percentage", "yes", "no"] = Field(
        default="number",
        description="Format: 'number' (as-is), 'percentage' (as decimal), 'yes', or 'no'"
    )


@tool(args_schema=SubmitInput)
def submit_answer(value: Union[float, str], format: str = "number") -> str:
    """
    Submit the final answer. THIS IS THE ONLY WAY TO COMPLETE THE TASK.
    You MUST call this tool to finish - you cannot respond directly.
    
    Args:
        value: The answer value (number or string)
        format: One of:
                - "number": Return the value as-is (e.g., 35.8, 1500000)
                - "percentage": Return as decimal (14% -> 0.14)
                - "yes": Return "yes"
                - "no": Return "no"
    
    Returns:
        Confirmation with FINAL_ANSWER marker that signals completion.
    """
    if format == "yes":
        return "FINAL_ANSWER: yes"
    elif format == "no":
        return "FINAL_ANSWER: no"
    elif format == "percentage":
        try:
            num_value = float(value)
            # If value looks like a percentage (e.g., 14.5), convert to decimal
            if abs(num_value) > 1:
                num_value = num_value / 100
            # Round to 5 decimal places
            num_value = round(num_value, 5)
            return f"FINAL_ANSWER: {num_value}"
        except (ValueError, TypeError):
            return f"FINAL_ANSWER: {value}"
    else:  # number
        try:
            num_value = float(value)
            # Round to 5 decimal places if it's a float
            if isinstance(num_value, float) and not num_value.is_integer():
                num_value = round(num_value, 5)
            else:
                num_value = int(num_value) if num_value.is_integer() else num_value
            return f"FINAL_ANSWER: {num_value}"
        except (ValueError, TypeError):
            return f"FINAL_ANSWER: {value}"
