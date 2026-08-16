"""
Unit tests for Step 6G Resumable Gemini Semantic Pilot.

Tests:
- Loading and deduplicating existing results from disk
- Skipping already completed message IDs
- Extracting only missing messages up to the requested target limit
- Immediate append-only file writes and flush behavior
- Graceful termination on quota / rate-limit errors while preserving previous results
- Partial failure preservation
- Handling empty and missing output files and auto-creating parent directories
- Deterministic candidate ordering
- 100% offline verification with mocked extractor
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
import pytest

from backend.semantic.pilot import (
    filter_pending_messages,
    is_quota_or_rate_limit_error,
    load_candidate_messages,
    load_existing_results,
    run_resumable_pilot,
)
from backend.semantic.schema import (
    SemanticEntity,
    SemanticExtraction,
    SemanticStatement,
)


class DummyMockExtractor:
    """Mock semantic extractor for deterministic offline testing."""

    def __init__(self, failure_on_msg_id: int | None = None, error_to_raise: Exception | None = None) -> None:
        self.call_count = 0
        self.extracted_msg_ids: list[int] = []
        self.failure_on_msg_id = failure_on_msg_id
        self.error_to_raise = error_to_raise or RuntimeError("Simulated extraction failure")

    def extract(self, message: dict[str, Any]) -> SemanticExtraction:
        self.call_count += 1
        msg_id = int(message["message_id"])
        doc_id = str(message["document_id"])

        if self.failure_on_msg_id is not None and msg_id == self.failure_on_msg_id:
            raise self.error_to_raise

        self.extracted_msg_ids.append(msg_id)

        return SemanticExtraction(
            message_id=msg_id,
            document_id=doc_id,
            entities=[
                SemanticEntity(type="Entity", name=f"Entity-{msg_id}", confidence=0.9)
            ],
            statements=[
                SemanticStatement(text=f"Statement for message {msg_id}", type="fact", confidence=0.95)
            ],
        )


@pytest.fixture
def temp_pilot_env(tmp_path: Path) -> tuple[Path, Path]:
    """Create a temporary input sample file and an output file path."""
    input_file = tmp_path / "sample.jsonl"
    output_file = tmp_path / "out" / "pilot_results.jsonl"

    sample_messages = [
        {
            "message_id": 1001 + i,
            "document_id": f"doc_{1001 + i}",
            "author": f"User{i}",
            "text": f"Sample message text {i}",
        }
        for i in range(10)
    ]

    with input_file.open("w", encoding="utf-8") as handle:
        for msg in sample_messages:
            handle.write(json.dumps(msg) + "\n")

    return input_file, output_file


def test_load_candidate_messages_limit_and_order(temp_pilot_env: tuple[Path, Path]) -> None:
    input_file, _ = temp_pilot_env
    candidates = load_candidate_messages(input_file=input_file, limit=5)

    assert len(candidates) == 5
    assert [c["message_id"] for c in candidates] == [1001, 1002, 1003, 1004, 1005]


def test_load_existing_results_empty_and_corrupt_lines(tmp_path: Path) -> None:
    out_file = tmp_path / "pilot.jsonl"
    # File doesn't exist
    records, ids = load_existing_results(out_file, fallback_file=None)
    assert records == []
    assert ids == set()

    # File with empty lines, comments/corrupted line, and duplicate IDs
    with out_file.open("w", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write(json.dumps({"message_id": 101, "document_id": "doc1"}) + "\n")
        handle.write("   \n")
        handle.write("CORRUPTED JSON LINE\n")
        handle.write(json.dumps({"message_id": 101, "document_id": "doc1_dup"}) + "\n")  # duplicate!
        handle.write(json.dumps({"message_id": 102, "document_id": "doc2"}) + "\n")

    records, ids = load_existing_results(out_file, fallback_file=None)
    assert len(records) == 2
    assert ids == {101, 102}
    assert records[0]["message_id"] == 101
    assert records[1]["message_id"] == 102


def test_filter_pending_messages() -> None:
    candidates = [
        {"message_id": 1},
        {"message_id": 2},
        {"message_id": 3},
        {"message_id": 4},
    ]
    completed = {2, 4}
    pending = filter_pending_messages(candidates, completed)
    assert [m["message_id"] for m in pending] == [1, 3]


def test_run_resumable_pilot_from_scratch(temp_pilot_env: tuple[Path, Path]) -> None:
    input_file, output_file = temp_pilot_env
    mock_extractor = DummyMockExtractor()

    # Run for limit 3
    results = run_resumable_pilot(
        input_file=input_file,
        output_file=output_file,
        limit=3,
        resume=True,
        extractor=mock_extractor,
    )

    assert len(results) == 3
    assert mock_extractor.call_count == 3
    assert [r["message_id"] for r in results] == [1001, 1002, 1003]
    assert output_file.exists()

    # Verify file contents on disk
    loaded_records, loaded_ids = load_existing_results(output_file, fallback_file=None)
    assert len(loaded_records) == 3
    assert loaded_ids == {1001, 1002, 1003}


def test_run_resumable_pilot_incremental_resume(temp_pilot_env: tuple[Path, Path]) -> None:
    input_file, output_file = temp_pilot_env

    # 1. First run: extract 3 messages
    extractor1 = DummyMockExtractor()
    run_resumable_pilot(
        input_file=input_file,
        output_file=output_file,
        limit=3,
        resume=True,
        extractor=extractor1,
    )
    assert extractor1.call_count == 3

    # 2. Second run: target 5 messages with resume=True
    extractor2 = DummyMockExtractor()
    results2 = run_resumable_pilot(
        input_file=input_file,
        output_file=output_file,
        limit=5,
        resume=True,
        extractor=extractor2,
    )

    # Extractor should ONLY be called for remaining 2 messages (1004, 1005)
    assert extractor2.call_count == 2
    assert extractor2.extracted_msg_ids == [1004, 1005]
    assert len(results2) == 5
    assert [r["message_id"] for r in results2] == [1001, 1002, 1003, 1004, 1005]

    # 3. Third run: target 5 messages (already satisfied)
    extractor3 = DummyMockExtractor()
    results3 = run_resumable_pilot(
        input_file=input_file,
        output_file=output_file,
        limit=5,
        resume=True,
        extractor=extractor3,
    )
    assert extractor3.call_count == 0  # no new extractions needed!
    assert len(results3) == 5


def test_quota_error_stops_cleanly_preserving_progress(temp_pilot_env: tuple[Path, Path]) -> None:
    input_file, output_file = temp_pilot_env

    class QuotaException(Exception):
        pass

    # Fails on message 1004 with 429 quota error
    extractor = DummyMockExtractor(
        failure_on_msg_id=1004,
        error_to_raise=QuotaException("ResourceExhausted: 429 Resource has been exhausted (e.g. check quota)"),
    )

    results = run_resumable_pilot(
        input_file=input_file,
        output_file=output_file,
        limit=6,
        resume=True,
        extractor=extractor,
    )

    # Messages 1001, 1002, 1003 should have succeeded and be saved to disk
    assert len(results) == 3
    assert [r["message_id"] for r in results] == [1001, 1002, 1003]

    # Verify disk contents survived
    records_on_disk, ids_on_disk = load_existing_results(output_file, fallback_file=None)
    assert len(records_on_disk) == 3
    assert ids_on_disk == {1001, 1002, 1003}


def test_unexpected_error_stops_and_preserves_progress(temp_pilot_env: tuple[Path, Path]) -> None:
    input_file, output_file = temp_pilot_env

    # Fails on message 1003 with unexpected error
    extractor = DummyMockExtractor(
        failure_on_msg_id=1003,
        error_to_raise=ValueError("Unexpected network socket error"),
    )

    results = run_resumable_pilot(
        input_file=input_file,
        output_file=output_file,
        limit=5,
        resume=True,
        extractor=extractor,
    )

    assert len(results) == 2
    assert [r["message_id"] for r in results] == [1001, 1002]


def test_is_quota_or_rate_limit_error_detection() -> None:
    assert is_quota_or_rate_limit_error(Exception("429 Too Many Requests"))
    assert is_quota_or_rate_limit_error(Exception("Quota exceeded for quota metric"))
    assert is_quota_or_rate_limit_error(Exception("google.genai.errors.ResourceExhausted"))
    assert is_quota_or_rate_limit_error(Exception("Rate limit reached"))
    assert not is_quota_or_rate_limit_error(ValueError("Invalid syntax"))
    assert not is_quota_or_rate_limit_error(KeyError("missing key"))
