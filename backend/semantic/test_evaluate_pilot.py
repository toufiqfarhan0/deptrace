"""
Unit tests for Step 6D Gemini Semantic Extraction Evaluation.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest

from backend.semantic.evaluate_pilot import (
    DEFAULT_INPUT_FILE,
    PilotEvaluationReport,
    evaluate_pilot,
    evaluate_results,
    load_results,
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
                    {"type": "Customer", "name": "ACME", "confidence": 0.9},
                    {"type": "Incident", "name": "502 Error", "confidence": 0.8},
                    {"type": "Customer", "name": "AuroraHealth", "confidence": 0.95},
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
                    {"type": "action", "text": "Rollback canary", "confidence": 0.95},
                    {"type": "action", "text": "Bump timeout", "confidence": 0.9},
                    {"type": "decision", "text": "Approve mitigation", "confidence": 0.85},
                    {"type": "fact", "text": "Latency back to normal", "confidence": 0.9},
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
                "entities": [{"type": "Entity", "name": "tool", "confidence": 0.9}],
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
                "message_id": 999,  # Mismatch!
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
                "document_id": "doc_mismatched",  # Mismatch!
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
                    {"type": "Entity", "name": "metrics API", "confidence": 0.9},
                    {"type": "Entity", "name": "trace_key", "confidence": 0.9},
                    {"type": "Entity", "name": "perf harness", "confidence": 0.9},
                    {"type": "Incident", "name": "latency surge", "confidence": 0.9},
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
                "statements": [{"type": "fact", "text": "hello", "confidence": 0.9}],
            },
        }
    ]
    report = evaluate_results(sample_records)
    assert report.total_entities == 0
    assert report.generic_entity_ratio == 0.0


def test_live_pilot_results_reproduction_if_exists() -> None:
    if not DEFAULT_INPUT_FILE.exists():
        pytest.skip(f"{DEFAULT_INPUT_FILE} does not exist on disk.")

    report = evaluate_pilot(DEFAULT_INPUT_FILE)
    assert report.messages_evaluated == 10
    assert report.provenance_errors == 0
    assert report.empty_entity_count == 2
    assert report.empty_statement_count == 1
    assert report.average_confidence == 0.923
    assert report.generic_entity_ratio == 0.8333
    assert report.entity_type_distribution["Entity"] == 20
    assert report.entity_type_distribution["ConfigurationChange"] == 3
    assert report.entity_type_distribution["Incident"] == 1
    assert report.statement_type_distribution["action"] == 15
    assert report.statement_type_distribution["claim"] == 4
    assert report.statement_type_distribution["fact"] == 3
    assert report.statement_type_distribution["decision"] == 2
    assert report.statement_type_distribution["outcome"] == 1
