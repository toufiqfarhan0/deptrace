"""
Offline unit tests for Step 6K fresh statement-to-entity (ABOUT) linking.

Validates:
- Deterministic 2-message selection fixture
- Bounded execution (strictly <= 2 calls) with mocked extractor
- Exact entity_ref matching against same-message entities
- Rejection/ignoring of unknown entity references
- Rejection of cross-message entity references
- Handling of duplicate and empty entity_refs
- Deterministic ABOUT relationship IDs
- Step 6K verifier execution and structural invariant validation
- 100% offline execution without calling Gemini API
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch
import pytest

from backend.semantic.fresh_entity_ref_pilot import run_fresh_pilot
from backend.semantic.fresh_entity_ref_sample import (
    TARGET_MESSAGE_IDS,
    select_fresh_sample,
)
from backend.semantic.ids import stable_id
from backend.semantic.ingest_semantic import (
    build_about_query,
    ingest_semantic_records,
)
from backend.semantic.schema import (
    SemanticEntity,
    SemanticExtraction,
    SemanticStatement,
)
from backend.semantic.verify_entity_refs import verify_fresh_entity_refs


class MockPilotExtractor:
    """Mock extractor for offline pilot execution."""

    def __init__(self, failure_index: int | None = None) -> None:
        self.call_count = 0
        self.failure_index = failure_index

    def extract(self, message: dict[str, Any]) -> SemanticExtraction:
        self.call_count += 1
        if self.failure_index is not None and self.call_count == self.failure_index:
            raise Exception("429 ResourceExhausted: Quota exceeded")

        msg_id = int(message["message_id"])
        doc_id = str(message["document_id"])

        return SemanticExtraction(
            message_id=msg_id,
            document_id=doc_id,
            entities=[
                SemanticEntity(
                    type="ConfigurationChange",
                    name=f"setting_{msg_id}",
                    confidence=0.95,
                ),
                SemanticEntity(
                    type="Entity",
                    name=f"Component-{msg_id}",
                    confidence=0.9,
                ),
            ],
            statements=[
                SemanticStatement(
                    text=f"Apply setting_{msg_id} to Component-{msg_id}.",
                    type="action",
                    confidence=0.95,
                    entity_refs=[f"setting_{msg_id}", f"Component-{msg_id}"],
                ),
                SemanticStatement(
                    text=f"General statement without entity references.",
                    type="fact",
                    confidence=0.8,
                    entity_refs=[],
                ),
            ],
        )


def test_select_fresh_sample_deterministic(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample_100.jsonl"
    out_file = tmp_path / "fresh_2_sample.jsonl"

    messages = [
        {"message_id": 111, "document_id": "doc_1", "text": "Msg 1"},
        {"message_id": 452542953563317559, "document_id": "doc_target1", "text": "Target 1"},
        {"message_id": 222, "document_id": "doc_2", "text": "Msg 2"},
        {"message_id": 8537794879600693670, "document_id": "doc_target2", "text": "Target 2"},
    ]

    with sample_file.open("w", encoding="utf-8") as handle:
        for msg in messages:
            handle.write(json.dumps(msg) + "\n")

    selected = select_fresh_sample(source_file=sample_file, output_file=out_file)
    assert len(selected) == 2
    assert [m["message_id"] for m in selected] == TARGET_MESSAGE_IDS
    assert out_file.exists()


def test_run_fresh_pilot_bounded_calls(tmp_path: Path) -> None:
    sample_file = tmp_path / "fresh_2_sample.jsonl"
    out_file = tmp_path / "fresh_2_results.jsonl"

    messages = [
        {"message_id": 101, "document_id": "doc_101", "text": "Msg 1"},
        {"message_id": 102, "document_id": "doc_102", "text": "Msg 2"},
        {"message_id": 103, "document_id": "doc_103", "text": "Msg 3"},
    ]
    with sample_file.open("w", encoding="utf-8") as handle:
        for msg in messages:
            handle.write(json.dumps(msg) + "\n")

    mock_extractor = MockPilotExtractor()
    results = run_fresh_pilot(
        input_file=sample_file,
        output_file=out_file,
        max_calls=2,
        extractor=mock_extractor,
    )

    # Strictly bounded to 2 calls
    assert mock_extractor.call_count == 2
    assert len(results) == 2
    assert [r["message_id"] for r in results] == [101, 102]


def test_run_fresh_pilot_quota_error_handling(tmp_path: Path) -> None:
    sample_file = tmp_path / "fresh_2_sample.jsonl"
    out_file = tmp_path / "fresh_2_results.jsonl"

    messages = [
        {"message_id": 101, "document_id": "doc_101", "text": "Msg 1"},
        {"message_id": 102, "document_id": "doc_102", "text": "Msg 2"},
    ]
    with sample_file.open("w", encoding="utf-8") as handle:
        for msg in messages:
            handle.write(json.dumps(msg) + "\n")

    # Fails on call 2 with quota error
    mock_extractor = MockPilotExtractor(failure_index=2)
    results = run_fresh_pilot(
        input_file=sample_file,
        output_file=out_file,
        max_calls=2,
        extractor=mock_extractor,
    )

    assert mock_extractor.call_count == 2
    assert len(results) == 1
    assert results[0]["message_id"] == 101


def test_about_linking_exact_same_message_and_isolation() -> None:
    """Validate that ABOUT links only form for exact entity names in the same message."""
    records = [
        {
            "message_id": 501,
            "document_id": "doc_501",
            "extraction": {
                "message_id": 501,
                "document_id": "doc_501",
                "entities": [
                    {"type": "ConfigurationChange", "name": "strict_model:true", "confidence": 0.95},
                ],
                "statements": [
                    {
                        "type": "action",
                        "text": "Enable strict_model:true in config.",
                        "confidence": 0.95,
                        "entity_refs": [
                            "strict_model:true",
                            "strict_model:true",  # duplicate ref
                            "NonExistentEntity",  # unknown ref
                            "Component-502",      # exists in msg 502, NOT in msg 501!
                        ],
                    },
                ],
            },
        },
        {
            "message_id": 502,
            "document_id": "doc_502",
            "extraction": {
                "message_id": 502,
                "document_id": "doc_502",
                "entities": [
                    {"type": "Entity", "name": "Component-502", "confidence": 0.9},
                ],
                "statements": [
                    {
                        "type": "fact",
                        "text": "Component-502 is operating normally.",
                        "confidence": 0.9,
                        "entity_refs": ["Component-502"],
                    },
                ],
            },
        },
    ]

    with patch("backend.semantic.ingest_semantic.run_query", return_value={"ok": True}) as mock_query:
        counts = ingest_semantic_records(records)
        assert counts["extractions"] == 2
        assert counts["entities"] == 2
        assert counts["statements"] == 2
        # Msg 501 statement: 1 ABOUT edge (strict_model:true only)
        # Msg 502 statement: 1 ABOUT edge (Component-502 only)
        # Total ABOUT edges = 2
        assert counts["about_links"] == 2


def test_build_about_query_deterministic_id() -> None:
    stmt_id = 9999
    entity = {
        "type": "Incident",
        "name": "INC-1234",
        "confidence": 0.95,
    }
    rel_id1, query1 = build_about_query(stmt_id, entity)
    rel_id2, query2 = build_about_query(stmt_id, entity)

    assert rel_id1 == rel_id2
    assert query1 == query2
    assert "-[:ABOUT {" in query1
    assert "INC-1234" in query1


def test_verify_fresh_entity_refs_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "non_existent.jsonl"
    stats = verify_fresh_entity_refs(missing_file)
    assert stats["extractions"] == 0
    assert stats["about_links"] == 0
    assert stats["provenance_errors"] == 0


def test_verify_fresh_entity_refs_mocked_success(tmp_path: Path) -> None:
    test_file = tmp_path / "fresh_mock.jsonl"
    records = [
        {
            "message_id": 901,
            "document_id": "doc_901",
            "extraction": {
                "message_id": 901,
                "document_id": "doc_901",
                "entities": [
                    {"type": "ConfigurationChange", "name": "setting_a", "confidence": 0.95}
                ],
                "statements": [
                    {"type": "action", "text": "Set setting_a.", "confidence": 0.9, "entity_refs": ["setting_a"]}
                ],
            },
        }
    ]
    with test_file.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Mock query responses for ingestion and verification
    mock_ext_rows = {
        "rows": [
            [{"value": 901}, {"value": 901}, {"value": "doc_901"}]
        ]
    }
    mock_about_count = {"rows": [[{"type": "integer", "value": 1}]]}
    mock_about_samples = {
        "rows": [
            [
                {"value": 111},
                {"value": "action"},
                {"value": 222},
                {"value": "setting_a"},
                {"value": "Set setting_a."},
            ]
        ]
    }

    with patch("backend.semantic.ingest_semantic.run_query", return_value={"ok": True}):
        with patch("backend.semantic.verify_entity_refs.query") as mock_q:
            mock_q.side_effect = [
                mock_ext_rows,
                mock_about_count,
                mock_about_samples,
            ]
            stats = verify_fresh_entity_refs(test_file)
            assert stats["extractions"] == 1
            assert stats["entities"] == 1
            assert stats["statements"] == 1
            assert stats["about_links"] == 1
            assert stats["provenance_errors"] == 0
