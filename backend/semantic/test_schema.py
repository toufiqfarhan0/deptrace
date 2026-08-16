from __future__ import annotations

import pytest

try:
    from backend.semantic.schema import (
        SemanticEntity,
        SemanticExtraction,
        SemanticStatement,
    )
except ImportError:
    from schema import (
        SemanticEntity,
        SemanticExtraction,
        SemanticStatement,
    )


def test_valid_entity() -> None:
    entity = SemanticEntity(
        type="Customer",
        name="ACME",
        confidence=0.95,
    )

    assert entity.name == "ACME"


def test_entity_confidence_must_be_valid() -> None:
    with pytest.raises(ValueError):
        SemanticEntity(
            type="Customer",
            name="ACME",
            confidence=1.5,
        )


def test_empty_entity_name_rejected() -> None:
    with pytest.raises(ValueError):
        SemanticEntity(
            type="Customer",
            name="",
            confidence=0.9,
        )


def test_valid_statement() -> None:
    statement = SemanticStatement(
        text="ACME experienced elevated latency.",
        type="fact",
        confidence=0.91,
    )

    assert statement.type == "fact"
    assert statement.entity_refs == []


def test_statement_entity_refs_default_empty() -> None:
    statement = SemanticStatement(
        text="All tests passed.",
        type="outcome",
        confidence=0.99,
    )
    assert statement.entity_refs == []


def test_statement_entity_refs_normalization_and_deduplication() -> None:
    statement = SemanticStatement(
        text="Rolled out strict_model:true for request-time guard.",
        type="action",
        confidence=0.95,
        entity_refs=[
            "  strict_model:true  ",
            "request-time guard",
            "",
            "   ",
            "strict_model:true",  # duplicate
            "request-time guard",  # duplicate
            "Grafana",
        ],
    )
    assert statement.entity_refs == [
        "strict_model:true",
        "request-time guard",
        "Grafana",
    ]


def test_statement_backward_compatibility_missing_entity_refs() -> None:
    data = {
        "text": "Legacy statement format without entity_refs.",
        "type": "claim",
        "confidence": 0.85,
    }
    statement = SemanticStatement.model_validate(data)
    assert statement.entity_refs == []


def test_valid_extraction() -> None:
    result = SemanticExtraction(
        message_id=123,
        document_id="doc-001",
        entities=[
            SemanticEntity(
                type="Customer",
                name="ACME",
                confidence=0.95,
            )
        ],
        statements=[
            SemanticStatement(
                text="ACME experienced elevated latency.",
                type="fact",
                confidence=0.91,
                entity_refs=["ACME"],
            )
        ],
    )

    assert result.message_id == 123
    assert result.document_id == "doc-001"
    assert len(result.entities) == 1
    assert len(result.statements) == 1
    assert result.statements[0].entity_refs == ["ACME"]


def test_negative_message_id_rejected() -> None:
    with pytest.raises(ValueError):
        SemanticExtraction(
            message_id=-1,
            document_id="doc-001",
        )