"""Table lookup tool for extracting values from document tables."""

from typing import Any, Optional


def lookup_table(
    table: dict[str, dict[str, Any]],
    row_key: str,
    column_key: Optional[str] = None,
) -> Any:
    """
    Look up a value in a document table.
    
    Args:
        table: Table data as nested dict {row: {col: value}}
        row_key: Row identifier to look up
        column_key: Optional column identifier. If None, returns entire row.
        
    Returns:
        Value at specified location, or None if not found.
        
    Examples:
        >>> table = {"2007": {"revenue": 100, "profit": 20}}
        >>> lookup_table(table, "2007", "revenue")
        100
        >>> lookup_table(table, "2007")
        {"revenue": 100, "profit": 20}
    """
    # Try exact match first
    if row_key in table:
        row = table[row_key]
        if column_key is None:
            return row
        return row.get(column_key)
    
    # Try case-insensitive match
    for key, row in table.items():
        if key.lower() == row_key.lower():
            if column_key is None:
                return row
            # Try case-insensitive column match
            for col, val in row.items():
                if col.lower() == column_key.lower():
                    return val
            return row.get(column_key)
    
    # Try partial match (row key contains search term)
    for key, row in table.items():
        if row_key.lower() in key.lower():
            if column_key is None:
                return row
            for col, val in row.items():
                if column_key.lower() in col.lower():
                    return val
    
    return None


def find_in_table(
    table: dict[str, dict[str, Any]],
    search_term: str,
) -> list[tuple[str, str, Any]]:
    """
    Find all occurrences of a search term in a table.
    
    Args:
        table: Table data as nested dict
        search_term: Term to search for in row/column names
        
    Returns:
        List of (row_key, column_key, value) tuples
    """
    results = []
    search_lower = search_term.lower()
    
    for row_key, row_data in table.items():
        if isinstance(row_data, dict):
            for col_key, value in row_data.items():
                if search_lower in row_key.lower() or search_lower in col_key.lower():
                    results.append((row_key, col_key, value))
    
    return results


def get_column_values(
    table: dict[str, dict[str, Any]],
    column_key: str,
) -> dict[str, Any]:
    """
    Get all values for a specific column across all rows.
    
    Args:
        table: Table data
        column_key: Column to extract
        
    Returns:
        Dict mapping row keys to column values
    """
    result = {}
    col_lower = column_key.lower()
    
    for row_key, row_data in table.items():
        if isinstance(row_data, dict):
            for col, val in row_data.items():
                if col_lower in col.lower():
                    result[row_key] = val
                    break
    
    return result
