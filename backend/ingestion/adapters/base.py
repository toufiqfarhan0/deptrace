"""
Base Source Adapter Interface for Enterprise Ingestion (Step 13B).
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from backend.ingestion.canonical import CanonicalRecord


class BaseAdapter(ABC):
    """
    Abstract base adapter for normalizing source-specific documents into CanonicalRecord.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the source: 'slack' | 'linear' | 'github'."""
        ...

    @abstractmethod
    def parse_content(self, filename: str, content: str) -> CanonicalRecord:
        """Parse raw text content into a CanonicalRecord."""
        ...

    def parse_file(self, file_path: Path) -> CanonicalRecord:
        """Read and parse a single document file."""
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return self.parse_content(filename=file_path.name, content=content)

    def iterate_records(
        self,
        source_dir: Path,
        limit: int | None = None,
    ) -> Iterator[CanonicalRecord]:
        """
        Deterministically iterate and parse files in the source directory.
        Files are processed in sorted order by filename for reproducibility.
        """
        if not source_dir.exists():
            return

        files = sorted(list(source_dir.glob("*.txt")))
        if limit is not None and limit > 0:
            files = files[:limit]

        for file_path in files:
            yield self.parse_file(file_path)

    @staticmethod
    def extract_dsid(filename: str) -> str:
        """Extract the dsid_<hex> prefix from standard EnterpriseRAG filenames."""
        if "__" in filename:
            return filename.split("__", 1)[0]
        return filename.rsplit(".", 1)[0]
