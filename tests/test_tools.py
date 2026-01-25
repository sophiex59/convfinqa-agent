import pytest
from src.tools.calculate import calculate
from src.tools.lookup_value import lookup_value, find_best_match

# --- calculate tests ---
def test_calculate_basic():
    assert "Result: 2" in calculate.invoke("1 + 1")
    assert "Result: 5.0" in calculate.invoke("10 / 2")
    assert "Result: 50.0" in calculate.invoke("100 * 0.5")

def test_calculate_error_handling():
    assert "Error: Division by zero" in calculate.invoke("1 / 0")
    assert "Error" in calculate.invoke("invalid syntax")
    assert "Error" in calculate.invoke("__import__('os')")

def test_calculate_complex():
    assert "Result: 7" in calculate.invoke("1 + 2 * 3")
    assert "Result: 9" in calculate.invoke("(1 + 2) * 3")

# --- lookup_value tests ---
@pytest.fixture
def sample_table():
    return {
        "Revenue": {"2018": "100", "2019": "200"},
        "Net Income": {"2018": "50", "2019": "60"},
        "Losses": {"2018": "(10)", "2019": "(20)"} 
    }

def test_lookup_value_exact(sample_table):
    from src.tools import set_table_context
    set_table_context(sample_table)
    # Must use invoke with dict for multi-arg tools
    assert "100" in lookup_value.invoke({"row": "Revenue", "column": "2018"})
    assert "60" in lookup_value.invoke({"row": "Net Income", "column": "2019"})

def test_lookup_value_fuzzy(sample_table):
    from src.tools import set_table_context
    set_table_context(sample_table)
    assert "100" in lookup_value.invoke({"row": "revenue", "column": "2018"})
    assert "50" in lookup_value.invoke({"row": "income", "column": "2018"})

def test_lookup_value_missing(sample_table):
    from src.tools import set_table_context
    set_table_context(sample_table)
    assert "Error: Row" in lookup_value.invoke({"row": "NonInternal", "column": "2018"})
    assert "Error: Column" in lookup_value.invoke({"row": "Revenue", "column": "2025"})

def test_lookup_value_no_context():
    from src.tools import set_table_context
    set_table_context(None)
    assert "Error: No table data" in lookup_value.invoke({"row": "Revenue", "column": "2018"})
