"""Submit answer tool - finalizes the agent's response."""

from typing import Literal, Union

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.core.utils import normalize_answer


class SubmitInput(BaseModel):
    """Input schema for submit_answer tool."""
    value: Union[float, str] = Field(description="The answer value")
    format: Literal["number", "percentage", "money", "yes", "no"] = Field(
        default="number",
        description="Format: 'number' (as-is), 'percentage' (as decimal), 'money' (converts billion/million to raw number), 'yes', or 'no'"
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
                - "money": Strips currency/text but preserves number ("2.2 billion" -> 2.2). YOU must convert if needed.
                - "yes": Return "yes"
                - "no": Return "no"

    Returns:
        Confirmation with FINAL_ANSWER marker that signals completion.
    """
    if format == "yes":
        return "FINAL_ANSWER: yes"
    elif format == "no":
        return "FINAL_ANSWER: no"

    # Use consolidated normalization logic
    norm_value = normalize_answer(value)
    return f"FINAL_ANSWER: {norm_value}"
