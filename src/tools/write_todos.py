"""Write todos tool - creates a plan for answering questions."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools.context import set_todos


class WriteTodosInput(BaseModel):
    """Input schema for write_todos tool."""
    steps: list[str] = Field(
        description="List of steps to complete, e.g. ['Look up 2007 revenue', 'Calculate change']"
    )


@tool(args_schema=WriteTodosInput)
def write_todos(steps: list[str]) -> str:
    """
    Create a detailed plan for answering the question.
    Call this FIRST to plan your approach before doing lookups or calculations.

    Args:
        steps: List of specific steps to complete, e.g.:
               ["Look up 2007 revenue in table",
                "Look up 2006 revenue in table",
                "Calculate the difference",
                "Calculate percentage change"]

    Returns:
        Confirmation of your plan.
    """
    set_todos(steps)
    plan_text = "Plan created:\n" + "\n".join(f"  {i+1}. {step}" for i, step in enumerate(steps))
    return plan_text
