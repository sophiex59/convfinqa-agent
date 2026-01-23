"""Shared context for agent tools.

This module manages global state that tools need access to,
such as the current table context and todo list.
"""

# Global state for tool execution
_current_table: dict = {}
_current_todos: list[str] = []


def set_table_context(table: dict) -> None:
    """Set the table context for tool calls."""
    global _current_table
    _current_table = table


def get_table_context() -> dict:
    """Get the current table context."""
    return _current_table


def get_todos() -> list[str]:
    """Get the current todo list."""
    return _current_todos.copy()


def set_todos(todos: list[str]) -> None:
    """Set the todo list."""
    global _current_todos
    _current_todos = todos


def clear_todos() -> None:
    """Clear the todo list."""
    global _current_todos
    _current_todos = []
