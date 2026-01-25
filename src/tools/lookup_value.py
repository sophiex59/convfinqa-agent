"""Lookup value tool - retrieves values from financial tables."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools.context import get_table_context


class LookupInput(BaseModel):
    """Input schema for lookup_value tool."""
    row: str = Field(description="Row identifier, e.g., '2007' or 'total revenue'")
    column: str = Field(description="Column identifier, e.g., 'revenue' or 'Q1'")


def normalize_key(key: str) -> str:
    """Normalize a key for fuzzy matching."""
    return str(key).lower().strip().replace("_", " ").replace("-", " ")


def find_best_match(target: str, candidates: list[str]) -> str | None:
    """Find the best matching key from candidates."""
    target_norm = normalize_key(target)

    # Exact match first
    for c in candidates:
        if normalize_key(c) == target_norm:
            return c

    # Substring match
    for c in candidates:
        c_norm = normalize_key(c)
        if target_norm in c_norm or c_norm in target_norm:
            return c

    # Word overlap match
    target_words = set(target_norm.split())
    best_match = None
    best_overlap = 0
    for c in candidates:
        c_words = set(normalize_key(c).split())
        overlap = len(target_words & c_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = c

    return best_match if best_overlap > 0 else None


@tool(args_schema=LookupInput)
def lookup_value(row: str, column: str) -> str:
    """
    Look up a specific value in the financial data table.

    Args:
        row: The row identifier (e.g., "2007", "total revenue", "net income")
        column: The column identifier (e.g., "amount", "Q1", "percentage")

    Returns:
        The value at the intersection of row and column, or an error message.
    """
    table = get_table_context()

    if not table:
        return "Error: No table data available"

    # Get available rows and columns
    available_rows = list(table.keys())
    first_row = table.get(available_rows[0], {}) if available_rows else {}
    list(first_row.keys()) if isinstance(first_row, dict) else []

    # Find matching row
    matched_row = find_best_match(row, available_rows)
    if not matched_row:
        return f"Error: Row '{row}' not found. Available rows: {available_rows[:5]}"

    row_data = table[matched_row]

    # Handle non-dict row data
    if not isinstance(row_data, dict):
        return f"Value for '{matched_row}': {row_data}"

    # Find matching column
    matched_column = find_best_match(column, list(row_data.keys()))
    if not matched_column:
        return f"Error: Column '{column}' not found in row '{matched_row}'. Available columns: {list(row_data.keys())[:5]}"

    value = row_data[matched_column]
    return f"Value at [{matched_row}, {matched_column}]: {value}"
