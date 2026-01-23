"""Data loading utilities for ConvFinQA dataset."""

import json
from pathlib import Path
from typing import Iterator

from src.core.schemas import ConvFinQARecord, ConvFinQADataset
from src.core.config import settings


class DataLoader:
    """Load and access ConvFinQA dataset."""

    def __init__(self, data_path: str | None = None):
        self.data_path = Path(data_path or settings.data_path)
        self._data: ConvFinQADataset | None = None

    def load(self) -> ConvFinQADataset:
        """Load dataset from JSON file."""
        if self._data is not None:
            return self._data

        with open(self.data_path) as f:
            raw_data = json.load(f)

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
