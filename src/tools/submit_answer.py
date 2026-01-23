"""Submit answer tool - finalizes the agent's response."""

from typing import Literal, Union

from langchain_core.tools import tool
from pydantic import BaseModel, Field


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
                - "money": Convert billion/million to raw number ("2.2 billion" -> 2200000000)
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
        # If value has % sign, convert to decimal (e.g., "142.4%" -> 1.424)
        # Otherwise, assume it's already a decimal (e.g., 1.42403)
        try:
            str_value = str(value).strip()
            if "%" in str_value:
                num_value = float(str_value.replace("%", "")) / 100
            else:
                num_value = float(str_value)
            num_value = round(num_value, 5)
            return f"FINAL_ANSWER: {num_value}"
        except (ValueError, TypeError):
            return f"FINAL_ANSWER: {value}"
    elif format == "money":
        # Convert billion/million text to millions (base unit in financial docs)
        # "2.2 billion" → 2200 (millions)
        # "3.5 million" → 3.5 (millions)
        try:
            str_value = str(value).strip().lower()
            str_value = str_value.replace("$", "").replace(",", "").strip()
            
            multiplier = 1  # Already in millions or raw number
            if "billion" in str_value:
                multiplier = 1000  # Convert billions to millions
                str_value = str_value.replace("billion", "").strip()
            elif "million" in str_value:
                multiplier = 1  # Already in millions
                str_value = str_value.replace("million", "").strip()
            
            num_value = float(str_value) * multiplier
            if num_value.is_integer():
                return f"FINAL_ANSWER: {int(num_value)}"
            return f"FINAL_ANSWER: {round(num_value, 5)}"
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
