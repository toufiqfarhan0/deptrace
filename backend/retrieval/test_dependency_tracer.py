"""
Offline unit tests for HydraDB Dependency Tracer (Step 11).

Validates:
1. Multi-hop dependency path resolution
2. Direct and indirect co-occurrence linking
3. Cycle protection and bounded depth traversal
4. Impact summary metrics aggregation
5. Chronological statement timeline ordering and deduplication
6. Non-existent and empty entity error handling
7. Available entity list retrieval
8. Provenance preservation across all trace nodes and hops
9. 100% offline execution with zero Gemini API calls
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
import pytest

from backend.retrieval.dependency_tracer import DependencyTracer
from backend.retrieval.models import (
    DependencyTraceRequest,
    DependencyTraceResponse,
    TraceHop,
    TraceImpactSummary,
)


def create_synthetic_query_fn() -> MagicMock:
    """Mock query_fn returning synthetic graph snapshot for testing."""

    def mock_query(query_str: str) -> dict[str, Any]:
        q = query_str.strip()
        if "HAS_SEMANTIC_EXTRACTION" in q:
            return {
                "rows": [
                    [{"value": 1001}, {"value": 5001}, {"value": "doc_alpha"}],
                    [{"value": 1002}, {"value": 5002}, {"value": "doc_beta"}],
                ]
            }
        elif "MENTIONS" in q:
            return {
                "rows": [
                    [{"value": 5001}, {"value": 9001}, {"value": "Service-A"}],
                    [{"value": 5001}, {"value": 9002}, {"value": "Service-B"}],
                    [{"value": 5002}, {"value": 9002}, {"value": "Service-B"}],
                    [{"value": 5002}, {"value": 9003}, {"value": "Service-C"}],
                ]
            }
        elif "EXPRESSES" in q:
            return {
                "rows": [
                    [{"value": 5001}, {"value": 7001}, {"value": "fact"}, {"value": "Service-A failed due to latency."}],
                    [{"value": 5001}, {"value": 7002}, {"value": "action"}, {"value": "Team restarted Service-B."}],
                    [{"value": 5002}, {"value": 7003}, {"value": "decision"}, {"value": "Service-C was deployed to fix Service-B."}],
                ]
            }
        elif "ABOUT" in q:
            return {
                "rows": [
                    [{"value": 7001}, {"value": "fact"}, {"value": "Service-A failed due to latency."}, {"value": 9001}, {"value": "Service-A"}],
                    [{"value": 7003}, {"value": "decision"}, {"value": "Service-C was deployed to fix Service-B."}, {"value": 9003}, {"value": "Service-C"}],
                ]
            }
        return {"rows": []}

    return MagicMock(side_effect=mock_query)


def test_dependency_trace_request_validation() -> None:
    req = DependencyTraceRequest(entity="REL-311", max_depth=2, limit=10)
    assert req.entity == "REL-311"
    assert req.max_depth == 2

    with pytest.raises(ValueError):
        DependencyTraceRequest(entity="   ")


def test_get_available_entities() -> None:
    tracer = DependencyTracer(query_fn=create_synthetic_query_fn())
    entities = tracer.get_available_entities()
    assert entities == ["Service-A", "Service-B", "Service-C"]


def test_trace_direct_and_multi_hop() -> None:
    tracer = DependencyTracer(query_fn=create_synthetic_query_fn())

    # Trace Service-A with depth=2:
    # Service-A -> Service-B (hop 1, msg 1001)
    # Service-B -> Service-C (hop 2, msg 1002)
    res = tracer.trace(entity="Service-A", max_depth=2)

    assert res.found is True
    assert res.root_entity == "Service-A"
    assert res.impact_summary.total_linked_entities == 2
    assert "Service-B" in res.impact_summary.affected_components
    assert "Service-C" in res.impact_summary.affected_components

    # Verify Hops
    hop_targets = {h.target_entity for h in res.dependency_hops}
    assert "Service-B" in hop_targets
    assert "Service-C" in hop_targets

    # Verify Timeline
    assert len(res.timeline) == 3
    assert res.timeline[0].order_index == 1
    assert res.timeline[0].message_id == 1001
    assert res.timeline[0].document_id == "doc_alpha"


def test_trace_cycle_protection() -> None:
    # Graph with cycle: Service-A <-> Service-B in message 1001
    tracer = DependencyTracer(query_fn=create_synthetic_query_fn())
    res = tracer.trace(entity="Service-A", max_depth=4)

    # Should not enter infinite loop, and should visit all 3 components
    assert res.found is True
    assert len(res.impact_summary.affected_components) == 2


def test_trace_non_existent_entity() -> None:
    tracer = DependencyTracer(query_fn=create_synthetic_query_fn())
    res = tracer.trace(entity="NonExistentService")

    assert res.found is False
    assert res.error is not None
    assert "NonExistentService" in res.error
    assert res.impact_summary.total_linked_entities == 0
    assert len(res.timeline) == 0
    assert len(res.dependency_hops) == 0


def test_trace_empty_entity_input() -> None:
    tracer = DependencyTracer(query_fn=create_synthetic_query_fn())
    res = tracer.trace(entity="")

    assert res.found is False
    assert res.error == "Target entity cannot be empty."


def test_trace_impact_summary_aggregation() -> None:
    tracer = DependencyTracer(query_fn=create_synthetic_query_fn())
    res = tracer.trace(entity="Service-B", max_depth=2)

    assert res.found is True
    summary = res.impact_summary
    assert summary.root_entity == "Service-B"
    assert summary.total_statements == 3
    assert summary.statements_by_type.get("fact") == 1
    assert summary.statements_by_type.get("action") == 1
    assert summary.statements_by_type.get("decision") == 1
    assert summary.affected_messages == [1001, 1002]
    assert summary.affected_documents == ["doc_alpha", "doc_beta"]


def test_trace_query_failure_handling() -> None:
    failing_query_fn = MagicMock(side_effect=RuntimeError("Connection refused"))
    tracer = DependencyTracer(query_fn=failing_query_fn)
    res = tracer.trace(entity="Service-A")

    assert res.found is False
    assert "Connection refused" in str(res.error)


def test_trace_provenance_integrity() -> None:
    tracer = DependencyTracer(query_fn=create_synthetic_query_fn())
    res = tracer.trace(entity="Service-A", max_depth=2)

    assert len(res.raw_evidence) > 0
    for ev in res.raw_evidence:
        assert ev.message_id in {1001, 1002}
        assert ev.document_id in {"doc_alpha", "doc_beta"}
        assert ev.match_type == "dependency_trace"
        assert ev.statement is not None
