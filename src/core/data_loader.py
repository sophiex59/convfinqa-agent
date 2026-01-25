"""Data loading utilities for ConvFinQA dataset."""

import json
import sys
from pathlib import Path
from typing import Iterator

from src.core.config import settings
from src.core.schemas import ConvFinQADataset, ConvFinQARecord
from src.logger import get_logger

logger = get_logger(__name__)

# ... existing imports ...

class DataLoader:
    """Load and access ConvFinQA dataset."""

    def __init__(self, data_path: str | None = None):
        self.data_path = Path(data_path or settings.data_path)
        self._data: ConvFinQADataset | None = None

    def load(self) -> ConvFinQADataset:
        """Load dataset from JSON file."""
        if self._data is not None:
            return self._data

        if not self.data_path.exists():
            logger.error(f"Dataset file not found: {self.data_path}")
            logger.error("Please ensure you have downloaded the dataset to the correct location.")
            sys.exit(1)

        try:
            with open(self.data_path) as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse dataset file: {self.data_path}")
            logger.error(f"JSON Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.exception(f"Unexpected error loading dataset: {e}")
            sys.exit(1)

        self._data = ConvFinQADataset(
            train=[ConvFinQARecord(**r) for r in raw_data["train"]],
            dev=[ConvFinQARecord(**r) for r in raw_data.get("dev", [])],
        )
        return self._data

    def get_record(self, record_id: str) -> ConvFinQARecord | None:
        """Get a specific record by ID."""
        data = self.load()
        for record in data.train + data.dev:
            if record.id == record_id:
                return record
        return None

    def iter_split(self, split: str = "dev") -> Iterator[ConvFinQARecord]:
        """Iterate over records in a split."""
        data = self.load()
        records = data.train if split == "train" else data.dev
        yield from records

    def get_sample(self, split: str = "dev", n: int = 10, offset: int = 0) -> list[ConvFinQARecord]:
        """Get a sample of records for testing.

        Args:
            split: Dataset split (train/dev)
            n: Number of records to return
            offset: Number of records to skip from the beginning
        """
        data = self.load()
        records = data.train if split == "train" else data.dev
        return records[offset:offset + n]


# Singleton data loader
data_loader = DataLoader()
