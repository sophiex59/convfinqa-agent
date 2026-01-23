"""Shared context for agent tools.

This module manages task-local state that tools need access to,
such as the current table context and todo list.

Uses contextvars for async-safe, task-local storage.
"""

from contextvars import ContextVar

# Task-local state for tool execution (async-safe)
_current_table: ContextVar[dict] = ContextVar("current_table", default={})
_current_todos: ContextVar[list[str]] = ContextVar("current_todos", default=[])


def set_table_context(table: dict) -> None:
    """Set the table context for tool calls (task-local)."""
    _current_table.set(table)


def get_table_context() -> dict:
    """Get the current table context."""
    return _current_table.get()


def get_todos() -> list[str]:
    """Get the current todo list."""
    return _current_todos.get().copy()


def set_todos(todos: list[str]) -> None:
    """Set the todo list."""
    _current_todos.set(todos)


def clear_todos() -> None:
    """Clear the todo list."""
    _current_todos.set([])
