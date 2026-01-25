import json
from unittest.mock import mock_open, patch

import pytest

from src.core.data_loader import DataLoader

DATA_CONTENT = {
    "train": [
        {
            "id": "train_1",
            "doc": {"pre_text": "text", "post_text": "text", "table": {}},
            "dialogue": {
                "conv_questions": ["q1"],
                "conv_answers": ["a1"],
                "turn_program": ["prog1"],
                "executed_answers": ["ans1"],
                "qa_split": [True]
            },
            "features": {
                "num_dialogue_turns": 1,
                "has_type2_question": False,
                "has_duplicate_columns": False,
                "has_non_numeric_values": False
            }
        }
    ],
    "dev": [
        {
            "id": "dev_1",
            "doc": {"pre_text": "text", "post_text": "text", "table": {}},
            "dialogue": {
                "conv_questions": ["q2"],
                "conv_answers": ["a2"],
                "turn_program": ["prog2"],
                "executed_answers": ["ans2"],
                "qa_split": [True]
            },
            "features": {
                "num_dialogue_turns": 1,
                "has_type2_question": False,
                "has_duplicate_columns": False,
                "has_non_numeric_values": False
            }
        }
    ]
}

@pytest.fixture
def mock_json_file():
    return json.dumps(DATA_CONTENT)

def test_load_success(mock_json_file):
    with patch("builtins.open", mock_open(read_data=mock_json_file)):
        with patch("pathlib.Path.exists", return_value=True):
            loader = DataLoader("dummy.json")
            data = loader.load()

            assert len(data.train) == 1
            assert len(data.dev) == 1
            assert data.train[0].id == "train_1"

def test_file_not_found():
    with patch("pathlib.Path.exists", return_value=False):
        loader = DataLoader("missing.json")
        with pytest.raises(SystemExit) as exc:
            loader.load()
        assert exc.value.code == 1

def test_json_decode_error():
    with patch("builtins.open", mock_open(read_data="invalid json")):
        with patch("pathlib.Path.exists", return_value=True):
            loader = DataLoader("bad.json")
            with pytest.raises(SystemExit) as exc:
                loader.load()
            assert exc.value.code == 1

def test_get_record(mock_json_file):
    with patch("builtins.open", mock_open(read_data=mock_json_file)):
        with patch("pathlib.Path.exists", return_value=True):
            loader = DataLoader("dummy.json")
            record = loader.get_record("dev_1")
            assert record is not None
            assert record.id == "dev_1"

            assert loader.get_record("missing_id") is None
