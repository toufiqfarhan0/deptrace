"""
Unit tests for Step 6D Gemini Semantic Extraction Evaluation.
"""

from __future__ import annotations

import pytest

from backend.semantic.evaluate_pilot import (
    DEFAULT_INPUT_FILE,
    LEGACY_INPUT_FILE,
    evaluate_pilot,
    evaluate_results,
)



def test_entity_type_counting() -> None:
    sample_records = [
        {
            "message_id": 1,
            "document_id": "doc1",
            "extraction": {
                "message_id": 1,
                "document_id": "doc1",
                "entities": [
                    {
                        "type": "Customer",
                        "name": "ACME",
                        "confidence": 0.9,
                    },
                    {
                        "type": "Incident",
                        "name": "502 Error",
                        "confidence": 0.8,
                    },
                    {
                        "type": "Customer",
                        "name": "AuroraHealth",
                        "confidence": 0.95,
                    },
                ],
                "statements": [],
            },
        }
    ]

    report = evaluate_results(sample_records)

    assert report.messages_evaluated == 1
    assert report.total_entities == 3
    assert report.entity_type_distribution["Customer"] == 2
    assert report.entity_type_distribution["Incident"] == 1
    assert report.generic_entity_ratio == 0.0


def test_statement_type_counting() -> None:
    sample_records = [
        {
            "message_id": 2,
            "document_id": "doc2",
            "extraction": {
                "message_id": 2,
                "document_id": "doc2",
                "entities": [],
                "statements": [
                    {
                        "type": "action",
                        "text": "Rollback canary",
                        "confidence": 0.95,
                    },
                    {
                        "type": "action",
                        "text": "Bump timeout",
                        "confidence": 0.9,
                    },
                    {
                        "type": "decision",
                        "text": "Approve mitigation",
                        "confidence": 0.85,
                    },
                    {
                        "type": "fact",
                        "text": "Latency back to normal",
                        "confidence": 0.9,
                    },
                ],
            },
        }
    ]

    report = evaluate_results(sample_records)

    assert report.messages_evaluated == 1
    assert report.total_statements == 4
    assert report.statement_type_distribution["action"] == 2
    assert report.statement_type_distribution["decision"] == 1
    assert report.statement_type_distribution["fact"] == 1


def test_empty_extraction_counts() -> None:
    sample_records = [
        {
            "message_id": 10,
            "document_id": "doc10",
            "extraction": {
                "message_id": 10,
                "document_id": "doc10",
                "entities": [],
                "statements": [],
            },
        },
        {
            "message_id": 11,
            "document_id": "doc11",
            "extraction": {
                "message_id": 11,
                "document_id": "doc11",
                "entities": [
                    {
                        "type": "Entity",
                        "name": "tool",
                        "confidence": 0.9,
                    }
                ],
                "statements": [],
            },
        },
    ]

    report = evaluate_results(sample_records)

    assert report.messages_evaluated == 2
    assert report.empty_entity_count == 1
    assert report.empty_statement_count == 2


def test_provenance_mismatch_detection() -> None:
    sample_records = [
        {
            "message_id": 100,
            "document_id": "doc_correct",
            "extraction": {
                "message_id": 999,
                "document_id": "doc_correct",
                "entities": [],
                "statements": [],
            },
        },
        {
            "message_id": 101,
            "document_id": "doc_original",
            "extraction": {
                "message_id": 101,
                "document_id": "doc_mismatched",
                "entities": [],
                "statements": [],
            },
        },
        {
            "message_id": 102,
            "document_id": "doc_valid",
            "extraction": {
                "message_id": 102,
                "document_id": "doc_valid",
                "entities": [],
                "statements": [],
            },
        },
    ]

    report = evaluate_results(sample_records)

    assert report.messages_evaluated == 3
    assert report.provenance_errors == 2


def test_generic_entity_ratio_calculation() -> None:
    sample_records = [
        {
            "message_id": 1,
            "document_id": "doc1",
            "extraction": {
                "message_id": 1,
                "document_id": "doc1",
                "entities": [
                    {
                        "type": "Entity",
                        "name": "metrics API",
                        "confidence": 0.9,
                    },
                    {
                        "type": "Entity",
                        "name": "trace_key",
                        "confidence": 0.9,
                    },
                    {
                        "type": "Entity",
                        "name": "perf harness",
                        "confidence": 0.9,
                    },
                    {
                        "type": "Incident",
                        "name": "latency surge",
                        "confidence": 0.9,
                    },
                ],
                "statements": [],
            },
        }
    ]

    report = evaluate_results(sample_records)

    assert report.total_entities == 4
    assert report.entity_type_distribution["Entity"] == 3

    # 3 / 4 = 0.75
    assert report.generic_entity_ratio == 0.75


def test_zero_entities_edge_case() -> None:
    sample_records = [
        {
            "message_id": 1,
            "document_id": "doc1",
            "extraction": {
                "message_id": 1,
                "document_id": "doc1",
                "entities": [],
                "statements": [
                    {
                        "type": "fact",
                        "text": "hello",
                        "confidence": 0.9,
                    }
                ],
            },
        }
    ]

    report = evaluate_results(sample_records)

    assert report.total_entities == 0
    assert report.generic_entity_ratio == 0.0


def test_live_pilot_results_reproduction_if_exists() -> None:
    """
    Validate stable invariants of the current live pilot.

    We intentionally do NOT assert exact entity/statement counts here.
    Gemini output can legitimately change when the extraction prompt,
    model, or taxonomy rules are refined.
    """

    if not DEFAULT_INPUT_FILE.exists() and not LEGACY_INPUT_FILE.exists():
        pytest.skip(
            f"Neither {DEFAULT_INPUT_FILE} nor {LEGACY_INPUT_FILE} exists on disk."
        )

    report = evaluate_pilot()


    # Stable structural invariants.
    assert report.messages_evaluated > 0

    # Provenance must always remain correct.
    assert report.provenance_errors == 0

    # Counts must remain valid.
    assert report.empty_entity_count >= 0
    assert report.empty_statement_count >= 0
    assert report.total_entities >= 0
    assert report.total_statements >= 0

    # Confidence is always normalized.
    assert 0.0 <= report.average_confidence <= 1.0

    # Generic entity ratio is normalized.
    assert 0.0 <= report.generic_entity_ratio <= 1.0

    # The distribution counts cannot exceed the totals.
    assert (
        sum(
            report.entity_type_distribution.values()
        )
        == report.total_entities
    )

    assert (
        sum(
            report.statement_type_distribution.values()
        )
        == report.total_statements
    )

    # A non-empty pilot should have at least one evaluated message.
    assert report.messages_evaluated > 0