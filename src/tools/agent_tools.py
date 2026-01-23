"""Agent tools for financial document QA using LangChain tool decorators."""

from typing import Literal, Union, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field


# Global reference to current table - set before agent invocation
_current_table: dict = {}
_current_todos: list[str] = []


def set_table_context(table: dict) -> None:
    """Set the table context for tool calls."""
    global _current_table
    _current_table = table


def get_todos() -> list[str]:
    """Get the current todo list."""
    return _current_todos.copy()


def clear_todos() -> None:
    """Clear the todo list."""
    global _current_todos
    _current_todos = []


class LookupInput(BaseModel):
    """Input for lookup_value tool."""
    row: str = Field(description="Row identifier, e.g., '2007' or 'total revenue'")
    column: str = Field(description="Column identifier, e.g., 'revenue' or 'Q1'")


class CalculateInput(BaseModel):
    """Input for calculate tool."""
    expression: str = Field(description="Mathematical expression, e.g., '60.94 - 25.14' or '(100-80)/80'")


class TodosInput(BaseModel):
    """Input for write_todos tool."""
    steps: list[str] = Field(description="List of steps to complete the task")


class SubmitInput(BaseModel):
    """Input for submit_answer tool."""
    value: Union[float, str] = Field(description="The answer value")
    format: Literal["number", "percentage", "yes", "no"] = Field(
        default="number",
        description="Answer format: 'number' (as-is), 'percentage' (as decimal), 'yes', 'no'"
    )


@tool(args_schema=LookupInput)
def lookup_value(row: str, column: str) -> str:
    """
    Look up a specific value from the financial table.
    Use this to extract exact values rather than guessing from the context.
    
    Args:
        row: Row identifier (e.g., "2007", "total revenue", "net income")
        column: Column identifier (e.g., "amount", "2019", "Q1")
    
    Returns:
        The value at that cell if found, otherwise an error message.
    
    Example:
        lookup_value("2007", "weighted average exercise price") → "60.94"
    """
    global _current_table
    
    if not _current_table:
        return "Error: No table context available"
    
    # Try exact match first
    if row in _current_table:
        row_data = _current_table[row]
        if isinstance(row_data, dict):
            if column in row_data:
                return str(row_data[column])
            # Try case-insensitive column match
            for col, val in row_data.items():
                if column.lower() in col.lower():
                    return str(val)
        return f"Error: Column '{column}' not found in row '{row}'. Available: {list(row_data.keys()) if isinstance(row_data, dict) else row_data}"
    
    # Try case-insensitive row match
    for key, row_data in _current_table.items():
        if row.lower() in key.lower():
            if isinstance(row_data, dict):
                if column in row_data:
                    return str(row_data[column])
                for col, val in row_data.items():
                    if column.lower() in col.lower():
                        return str(val)
            return f"Error: Column '{column}' not found. Available: {list(row_data.keys()) if isinstance(row_data, dict) else row_data}"
    
    available_rows = list(_current_table.keys())
    return f"Error: Row '{row}' not found. Available rows: {available_rows}"


@tool(args_schema=CalculateInput)
def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.
    Use this for ALL arithmetic - do not compute mentally.
    
    Args:
        expression: Math expression using +, -, *, /, and parentheses.
                   Use values from lookup_value results.
    
    Returns:
        The computed result as a number.
    
    Examples:
        calculate("60.94 - 25.14") → "35.8"
        calculate("(60.94 - 25.14) / 25.14") → "1.4240"
    """
    import re
    
    try:
        expr = expression.strip()
        
        # Remove currency symbols and commas
        expr = re.sub(r'[\$,]', '', expr)
        
        # Handle percentages (convert 25% to 0.25)
        expr = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'(\1/100)', expr)
        
        # Only allow safe characters
        allowed = set('0123456789.+-*/() ')
        if not all(c in allowed for c in expr):
            return f"Error: Invalid characters in expression. Only numbers and +-*/() allowed."
        
        # Evaluate safely
        result = eval(expr, {"__builtins__": {}}, {})
        
        return str(round(float(result), 6))
        
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: Could not evaluate '{expression}': {e}"


@tool(args_schema=TodosInput)
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
    global _current_todos
    _current_todos = steps
    
    plan_text = "Plan created:\n" + "\n".join(f"  {i+1}. {step}" for i, step in enumerate(steps))
    return plan_text


@tool(args_schema=SubmitInput)
def submit_answer(value: Union[float, str], format: str = "number") -> str:
    """
    Submit the final answer. THIS IS THE ONLY WAY TO COMPLETE THE TASK.
    You MUST call this tool to finish - you cannot respond directly.
    
    Args:
        value: The answer value (number or string)
        format: One of:
                - "number": Return the value as-is (e.g., 35.8, 1500000)
                - "percentage": Return as decimal (e.g., 0.14 for 14%)
                - "yes": Boolean yes response
                - "no": Boolean no response
    
    Returns:
        Confirmation that the answer was submitted.
    
    Examples:
        submit_answer(35.8, "number") → submits "35.8"
        submit_answer(0.1424, "percentage") → submits "0.1424"
        submit_answer(True, "yes") → submits "yes"
    """
    if format == "yes":
        final_value = "yes"
    elif format == "no":
        final_value = "no"
    elif format == "percentage":
        # Ensure it's a decimal
        try:
            num = float(value)
            # If value looks like a percentage (e.g., 14.24), convert to decimal
            if abs(num) > 2:
                num = num / 100
            final_value = str(round(num, 6))
        except:
            final_value = str(value)
    else:
        # number format
        try:
            final_value = str(round(float(value), 6))
        except:
            final_value = str(value)
    
    return f"FINAL_ANSWER:{final_value}"


# List of all tools for agent binding
AGENT_TOOLS = [write_todos, lookup_value, calculate, submit_answer]
