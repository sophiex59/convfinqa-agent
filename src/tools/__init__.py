"""Agent tools for financial document QA.

This package provides LangChain-compatible tools for the ReAct agent:
- write_todos: Create a planning checklist
- lookup_value: Look up values in financial tables  
- calculate: Perform arithmetic calculations
- submit_answer: Submit the final answer

Usage:
    from src.tools import AGENT_TOOLS, set_table_context, get_todos, clear_todos
"""

from src.tools.context import (
    set_table_context,
    get_table_context,
    get_todos,
    set_todos,
    clear_todos,
)
from src.tools.write_todos import write_todos
from src.tools.lookup_value import lookup_value
from src.tools.calculate import calculate
from src.tools.submit_answer import submit_answer

# All tools available to the agent
AGENT_TOOLS = [write_todos, lookup_value, calculate, submit_answer]

__all__ = [
    # Tools
    "AGENT_TOOLS",
    "write_todos",
    "lookup_value", 
    "calculate",
    "submit_answer",
    # Context management
    "set_table_context",
    "get_table_context",
    "get_todos",
    "set_todos",
    "clear_todos",
]
