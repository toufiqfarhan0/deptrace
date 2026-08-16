"""
Unit tests for Step 6J Gemini Semantic Ingestion into HydraDB.

Validates:
- Deterministic ID generation for semantic nodes and relationships
- Supported one-hop MERGE query formatting and escaping
- Statement -> ABOUT -> Entity one-hop MERGE relationship generation
- Exact same-message entity matching for entity_refs
- Provenance preservation and validation
- Handling empty entity and statement lists
- Offline validation of existing pilot records
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from backend.semantic.ids import stable_id
from backend.semantic.ingest_semantic import (
    DEFAULT_INPUT_FILE,
    LEGACY_INPUT_FILE,
    VALID_ENTITY_TYPES,
    VALID_STATEMENT_TYPES,
    build_about_query,
    build_entity_query,
    build_semantic_extraction_query,
    build_statement_query,
    cypher_string,
    ingest_semantic_records,
    load_records,
    validate_identifier,
)


def test_stable_id_deterministic() -> None:
    """Validate that stable_id is deterministic and respects namespace."""
    id1 = stable_id("Customer", "ACME")
    id2 = stable_id("Customer", "ACME")
    id3 = stable_id("Project", "ACME")
    id4 = stable_id("Customer", "acme")  # case-insensitive check

    assert id1 == id2
    assert id1 == id4
    assert id1 != id3
    assert 0 <= id1 <= 0x7FFFFFFFFFFFFFFF
    assert 0 <= id3 <= 0x7FFFFFFFFFFFFFFF


def test_stable_statement_and_rel_ids() -> None:
    """Validate deterministic IDs for statements and relationships."""
    ext_id = stable_id("semantic-extraction", "12345")
    stmt_id = stable_id("statement", f"{ext_id}:1:fact:latency is 5ms")
    rel_id = stable_id("relationship", f"semantic-extraction:{ext_id}:expresses:{stmt_id}")

    assert isinstance(stmt_id, int) and stmt_id >= 0
    assert isinstance(rel_id, int) and rel_id >= 0


def test_cypher_string_escaping() -> None:
    """Validate proper string escaping for Cypher injection safety."""
    assert cypher_string("hello") == "'hello'"
    assert cypher_string("hello 'world'") == "'hello \\'world\\''"
    assert cypher_string("back\\slash") == "'back\\\\slash'"


def test_validate_identifier() -> None:
    """Validate identifier checks."""
    assert validate_identifier("Customer") == "Customer"
    assert validate_identifier("ConfigurationChange") == "ConfigurationChange"
    assert validate_identifier("Entity") == "Entity"

    with pytest.raises(ValueError):
        validate_identifier("")

    with pytest.raises(ValueError):
        validate_identifier("Invalid-Identifier")

    with pytest.raises(ValueError):
        validate_identifier("123NumberStart")


def test_build_semantic_extraction_query() -> None:
    """Validate Message -> SemanticExtraction one-hop MERGE query."""
    msg_id = 4753520929491570635
    doc_id = "dsid_04be60269b524a158dcf09bb2f9bf752__1773541200-embed-batch-fallback-dim-conflict"

    ext_id, rel_id, query = build_semantic_extraction_query(msg_id, doc_id)

    assert ext_id >= 0
    assert rel_id >= 0
    assert "MERGE" in query
    assert f"(m:Message {{\n        id: {msg_id}\n    }})" in query
    assert f"-[:HAS_SEMANTIC_EXTRACTION {{\n        id: {rel_id}\n    }}]->" in query
    assert f"(x:SemanticExtraction {{\n        id: {ext_id}," in query
    assert f"message_id: {msg_id}," in query
    assert f"document_id: '{doc_id}'" in query


def test_build_entity_query() -> None:
    """Validate SemanticExtraction -> Entity one-hop MERGE query."""
    ext_id = 10001
    entity = {
        "type": "ConfigurationChange",
        "name": "strict_model:true",
        "confidence": 0.95,
    }

    ent_id, rel_id, query = build_entity_query(ext_id, entity)

    assert ent_id >= 0
    assert rel_id >= 0
    assert "MERGE" in query
    assert f"(x:SemanticExtraction {{\n        id: {ext_id}\n    }})" in query
    assert f"-[:MENTIONS {{\n        id: {rel_id},\n        confidence: 0.95\n    }}]->" in query
    assert f"(e:ConfigurationChange {{\n        id: {ent_id},\n        name: 'strict_model:true'\n    }})" in query


def test_build_statement_query() -> None:
    """Validate SemanticExtraction -> Statement one-hop MERGE query."""
    ext_id = 10001
    statement = {
        "type": "action",
        "text": "Prototype a fallback rule snippet",
        "confidence": 1.0,
    }

    stmt_id, rel_id, query = build_statement_query(ext_id, statement, index=1)

    assert stmt_id >= 0
    assert rel_id >= 0
    assert "MERGE" in query
    assert f"(x:SemanticExtraction {{\n        id: {ext_id}\n    }})" in query
    assert f"-[:EXPRESSES {{\n        id: {rel_id},\n        confidence: 1.0\n    }}]->" in query
    assert f"(s:Statement {{\n        id: {stmt_id},\n        statement_type: 'action',\n        text: 'Prototype a fallback rule snippet'\n    }})" in query


def test_build_about_query() -> None:
    """Validate Statement -> ABOUT -> Entity one-hop MERGE query."""
    stmt_id = 55555
    entity = {
        "type": "ConfigurationChange",
        "name": "strict_model:true",
        "confidence": 0.95,
    }

    rel_id, query = build_about_query(stmt_id, entity)

    assert rel_id >= 0
    assert "MERGE" in query
    assert f"(s:Statement {{\n        id: {stmt_id}\n    }})" in query
    assert f"-[:ABOUT {{\n        id: {rel_id}\n    }}]->" in query
    assert f"name: 'strict_model:true'" in query
    assert f"(e:ConfigurationChange" in query


def test_invalid_entity_or_statement_rejected() -> None:
    """Validate rejection of invalid entity types, statement types, or empty values."""
    ext_id = 10001

    with pytest.raises(ValueError, match="Unsupported semantic entity type"):
        build_entity_query(ext_id, {"type": "UnknownType", "name": "foo"})

    with pytest.raises(ValueError, match="Semantic entity name cannot be empty"):
        build_entity_query(ext_id, {"type": "Customer", "name": "   "})

    with pytest.raises(ValueError, match="Unsupported statement type"):
        build_statement_query(ext_id, {"type": "invalid_stmt", "text": "foo"}, 1)

    with pytest.raises(ValueError, match="Statement text cannot be empty"):
        build_statement_query(ext_id, {"type": "fact", "text": "   "}, 1)

    with pytest.raises(ValueError, match="Unsupported semantic entity type"):
        build_about_query(12345, {"type": "UnknownType", "name": "foo"})

    with pytest.raises(ValueError, match="Semantic entity name cannot be empty"):
        build_about_query(12345, {"type": "Customer", "name": "   "})


def test_existing_pilot_records_offline_validation() -> None:
    """
    Validate existing pilot records from pilot_results.jsonl or pilot_10_results.jsonl offline:
    - Non-empty record list
    - Zero provenance errors
    - Valid entity types and confidence scores
    - Valid statement types and confidence scores
    """
    if not DEFAULT_INPUT_FILE.exists() and not LEGACY_INPUT_FILE.exists():
        pytest.skip(f"Neither {DEFAULT_INPUT_FILE} nor {LEGACY_INPUT_FILE} exists.")

    records = load_records()
    assert len(records) > 0

    total_entities = 0
    total_statements = 0
    provenance_errors = 0

    for record in records:
        msg_id = record["message_id"]
        doc_id = record["document_id"]
        extraction = record["extraction"]

        # Provenance verification
        if extraction.get("message_id") != msg_id or extraction.get("document_id") != doc_id:
            provenance_errors += 1

        entities = extraction.get("entities", [])
        statements = extraction.get("statements", [])

        for ent in entities:
            assert ent["type"] in VALID_ENTITY_TYPES
            assert len(ent["name"].strip()) > 0
            assert 0.0 <= ent["confidence"] <= 1.0
            total_entities += 1

        for stmt in statements:
            assert stmt["type"] in VALID_STATEMENT_TYPES
            assert len(stmt["text"].strip()) > 0
            assert 0.0 <= stmt["confidence"] <= 1.0
            total_statements += 1

    assert provenance_errors == 0
    assert total_entities >= 0
    assert total_statements >= 0


def test_ingest_semantic_records_idempotent_mocked() -> None:
    """Validate ingestion counts and idempotency with mocked database."""
    if not DEFAULT_INPUT_FILE.exists() and not LEGACY_INPUT_FILE.exists():
        pytest.skip(f"Neither {DEFAULT_INPUT_FILE} nor {LEGACY_INPUT_FILE} exists.")

    records = load_records()
    expected_entities = sum(len(r.get("extraction", {}).get("entities", [])) for r in records)
    expected_statements = sum(len(r.get("extraction", {}).get("statements", [])) for r in records)

    with patch("backend.semantic.ingest_semantic.run_query", return_value={"ok": True}) as mock_query:
        counts1 = ingest_semantic_records(records)
        assert counts1["extractions"] == len(records)
        assert counts1["entities"] == expected_entities
        assert counts1["statements"] == expected_statements
        assert mock_query.call_count == len(records) + expected_entities + expected_statements

        mock_query.reset_mock()
        counts2 = ingest_semantic_records(records)
        assert counts2 == counts1
        assert mock_query.call_count == len(records) + expected_entities + expected_statements


def test_ingest_semantic_records_about_linking_mocked() -> None:
    """Validate that ABOUT edges are created for exact same-message matches and skipped otherwise."""
    synthetic_records = [
        {
            "message_id": 9901,
            "document_id": "doc_9901",
            "extraction": {
                "message_id": 9901,
                "document_id": "doc_9901",
                "entities": [
                    {"type": "ConfigurationChange", "name": "strict_model:true", "confidence": 0.95},
                    {"type": "Entity", "name": "Grafana", "confidence": 0.9},
                ],
                "statements": [
                    {
                        "type": "action",
                        "text": "Enable strict_model:true flag.",
                        "confidence": 0.95,
                        "entity_refs": ["strict_model:true", "UnknownEntity", "strict_model:true"],  # duplicate + unknown
                    },
                    {
                        "type": "fact",
                        "text": "General discussion without entity refs.",
                        "confidence": 0.8,
                        "entity_refs": [],
                    },
                    {
                        "type": "claim",
                        "text": "Grafana shows latency reduction after strict_model:true rollout.",
                        "confidence": 0.9,
                        "entity_refs": ["Grafana", "strict_model:true"],
                    },
                ],
            },
        }
    ]

    with patch("backend.semantic.ingest_semantic.run_query", return_value={"ok": True}) as mock_query:
        counts = ingest_semantic_records(synthetic_records)
        assert counts["extractions"] == 1
        assert counts["entities"] == 2
        assert counts["statements"] == 3
        # Statement 1 matched strict_model:true (1 edge)
        # Statement 2 had no refs (0 edges)
        # Statement 3 matched Grafana + strict_model:true (2 edges)
        # Total ABOUT edges = 3
        assert counts["about_links"] == 3
        # Total queries: 1 extraction + 2 entities + 3 statements + 3 about edges = 9
        assert mock_query.call_count == 9
