from src.core.utils import normalize_answer


def test_normalize_answer_basic():
    assert normalize_answer(123) == 123
    assert normalize_answer(123.45) == 123.45
    assert normalize_answer("123.45") == 123.45

def test_normalize_answer_currency():
    assert normalize_answer("$1,234.56") == 1234.56
    assert normalize_answer("$ 500") == 500.0

def test_normalize_answer_percentage():
    assert normalize_answer("50%") == 0.5
    assert normalize_answer("12.5%") == 0.125
    assert normalize_answer("100%") == 1.0

def test_normalize_answer_multipliers():
    # Base unit is assumed to be millions
    assert normalize_answer("5 million") == 5.0
    assert normalize_answer("1.5 million") == 1.5

    # Billions are scaled by 1000
    assert normalize_answer("2 billion") == 2000.0
    assert normalize_answer("0.5 billion") == 500.0
    assert normalize_answer("$ 3.2 billion") == 3200.0

def test_normalize_answer_mixed():
    # Percentage with other chars
    assert normalize_answer("approx 12.5 %") == 0.125

    # Negative values
    assert normalize_answer("-10.5") == -10.5
    assert normalize_answer("($500)") == -500.0

def test_normalize_answer_non_numeric():
    assert normalize_answer("yes") == "yes"
    assert normalize_answer("no data") == "no data"
    assert normalize_answer(None) == ""
