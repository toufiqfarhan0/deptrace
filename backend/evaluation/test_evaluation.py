"""
Offline unit tests for HydraDB Evaluation, Provenance Invariants, and Ablation (Step 12).

Validates:
1. Evaluation runner execution across benchmark queries
2. Provenance invariant checks (catching missing message_id or document_id)
3. Ablation comparison calculation
4. 100% offline execution with zero Gemini API calls
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
import pytest

from backend.evaluation.evaluation_runner import (
    EvaluationRunner,
    verify_provenance_invariants,
)
from backend.evaluation.models import EvaluationReport, ProvenanceCheckResult
from backend.retrieval.models import EvidenceItem, TraceHop


def create_synthetic_query_fn() -> MagicMock:
    """Mock query_fn returning synthetic graph snapshot for testing."""

    def mock_query(query_str: str) -> dict[str, Any]:
        q = query_str.strip()
        if "HAS_SEMANTIC_EXTRACTION" in q:
            return {
                "rows": [
                    [{"value": 8537794879600693670}, {"value": 5001}, {"value": "doc_alpha"}],
                    [{"value": 1050119542396350916}, {"value": 5002}, {"value": "doc_beta"}],
                ]
            }
        elif "MENTIONS" in q:
            return {
                "rows": [
                    [{"value": 5001}, {"value": 9001}, {"value": "REL-311"}],
                    [{"value": 5001}, {"value": 9002}, {"value": "api-search"}],
                    [{"value": 5002}, {"value": 9003}, {"value": "kernel-selector"}],
                ]
            }
        elif "EXPRESSES" in q:
            return {
                "rows": [
                    [{"value": 5001}, {"value": 7001}, {"value": "fact"}, {"value": "Support ticket REL-311 has been created."}],
                    [{"value": 5002}, {"value": 7002}, {"value": "action"}, {"value": "Revert kernel-selector if regression persists."}],
                ]
            }
        elif "ABOUT" in q:
            return {
                "rows": [
                    [{"value": 7001}, {"value": "fact"}, {"value": "Support ticket REL-311 has been created."}, {"value": 9001}, {"value": "REL-311"}],
                    [{"value": 7002}, {"value": "action"}, {"value": "Revert kernel-selector if regression persists."}, {"value": 9003}, {"value": "kernel-selector"}],
                ]
            }
        return {"rows": []}

    return MagicMock(side_effect=mock_query)


def test_provenance_invariant_verification_valid() -> None:
    evidence = [
        EvidenceItem(
            message_id=8537794879600693670,
            document_id="doc_alpha",
            entity_name="REL-311",
            statement="Support ticket REL-311 created",
            statement_type="fact",
            relationship="ABOUT",
        )
    ]
    hops = [
        TraceHop(
            source_entity="REL-311",
            target_entity="api-search",
            hop_distance=1,
            via_message_id=8537794879600693670,
            document_id="doc_alpha",
        )
    ]
    result = verify_provenance_invariants(evidence_items=evidence, hops=hops)
    assert result.is_valid is True
    assert result.missing_message_ids == 0
    assert result.missing_document_ids == 0
    assert result.total_items_checked == 2


def test_provenance_invariant_verification_missing_message_id() -> None:
    # Invalid evidence with message_id=0
    evidence = [
        EvidenceItem(
            message_id=0,
            document_id="doc_alpha",
            entity_name="REL-311",
        )
    ]
    result = verify_provenance_invariants(evidence_items=evidence)
    assert result.is_valid is False
    assert result.missing_message_ids == 1
    assert len(result.errors) == 1


def test_provenance_invariant_verification_missing_document_id() -> None:
    # Invalid evidence with empty document_id
    evidence = [
        EvidenceItem(
            message_id=8537794879600693670,
            document_id="",
            entity_name="REL-311",
        )
    ]
    result = verify_provenance_invariants(evidence_items=evidence)
    assert result.is_valid is False
    assert result.missing_document_ids == 1
    assert len(result.errors) == 1


def test_evaluation_runner_synthetic() -> None:
    runner = EvaluationRunner(query_fn=create_synthetic_query_fn())
    report = runner.run_evaluation(
        queries=[
            {"query": "What happened with REL-311?", "target_entity": "REL-311"},
            {"query": "What is connected to kernel-selector?", "target_entity": "kernel-selector"},
        ]
    )

    assert isinstance(report, EvaluationReport)
    assert report.total_queries == 2
    assert report.successful_queries == 2
    assert report.provenance_integrity.is_valid is True
    assert len(report.query_results) == 2
    assert len(report.ablation_comparisons) == 2

    # Check first query result
    q1 = report.query_results[0]
    assert q1.query == "What happened with REL-311?"
    assert q1.target_entity == "REL-311"
    assert q1.evidence_count > 0
    assert "REL-311" in q1.matched_entities

    # Check ablation
    ab1 = report.ablation_comparisons[0]
    assert ab1.text_has_graph_relationships is False
    assert ab1.text_has_typed_statements is False
    assert "ABOUT" in ab1.structural_advantage_summary
