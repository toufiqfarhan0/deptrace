from __future__ import annotations

import json
from pathlib import Path
import pytest

from backend.semantic.schema import (
    EntityType,
    SemanticEntity,
    SemanticExtraction,
    SemanticStatement,
    StatementType,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PILOT_RESULTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "pilot_10_results.jsonl"
)


def test_pilot_10_results_validation_if_exists() -> None:
    if not PILOT_RESULTS_FILE.exists():
        pytest.skip(f"{PILOT_RESULTS_FILE} does not exist on disk.")

    records = []
    with PILOT_RESULTS_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    assert len(records) > 0, f"Expected at least 1 pilot record, got {len(records)}"

    for record in records:
        assert "message_id" in record
        assert "document_id" in record
        assert "source_message" in record
        assert "extraction" in record

        # Validate extraction via Pydantic model
        extraction = SemanticExtraction.model_validate(record["extraction"])

        # Validate provenance preservation
        assert extraction.message_id == record["message_id"]
        assert extraction.document_id == record["document_id"]
        assert extraction.message_id >= 0
        assert len(extraction.document_id) > 0

        # Validate entities
        for entity in extraction.entities:
            assert isinstance(entity.name, str) and len(entity.name.strip()) > 0
            assert entity.type in {
                "Customer",
                "Project",
                "Incident",
                "Decision",
                "ConfigurationChange",
                "Entity",
            }
            assert 0.0 <= entity.confidence <= 1.0

        # Validate statements
        for statement in extraction.statements:
            assert isinstance(statement.text, str) and len(statement.text.strip()) > 0
            assert statement.type in {
                "fact",
                "decision",
                "claim",
                "action",
                "outcome",
            }
            assert 0.0 <= statement.confidence <= 1.0
