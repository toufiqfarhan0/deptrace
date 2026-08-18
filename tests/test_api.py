"""
Offline integration tests for DeTrace FastAPI web application & Dependency Tracing (Step 9 / Step 11).

Validates:
- GET /api/health with healthy and degraded HydraDB states
- POST /api/ask with grounded, ungrounded, and offline fallback scenarios
- GET /api/trace/entities returns list of available graph entities
- POST /api/trace returns multi-hop dependency hops and impact metrics
- Validation errors for empty/whitespace questions and entities
- Static frontend index.html and asset serving
- 100% offline execution with zero Gemini API calls
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.rag.models import AnswerResponse
from backend.retrieval.models import (
    DependencyTraceResponse,
    EvidenceItem,
    RetrievalResponse,
    StatementTimelineItem,
    TraceHop,
    TraceImpactSummary,
)


@pytest.fixture(autouse=True)
def isolate_local_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HYDRA_MODE", "local")


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_health_endpoint_healthy(client: TestClient) -> None:
    mock_query = MagicMock(return_value={"rows": [[{"value": 10}]]})
    with patch("backend.retrieval.factory.local_query_fn", mock_query):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "ok" in data["hydradb"]


def test_health_endpoint_degraded(client: TestClient) -> None:
    mock_query = MagicMock(side_effect=RuntimeError("HydraDB offline"))
    with patch("backend.retrieval.factory.local_query_fn", mock_query):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "degraded"
        assert "unreachable" in data["hydradb"]


def test_ask_endpoint_grounded_success(client: TestClient) -> None:
    mock_evidence = [
        EvidenceItem(
            message_id=8537794879600693670,
            document_id="doc_beta",
            entity_name="REL-311",
            statement="Support ticket REL-311 has been created.",
            statement_type="fact",
            relationship="ABOUT",
            match_type="exact_entity",
        )
    ]

    mock_rag_response = AnswerResponse(
        question="What happened with REL-311?",
        answer="Support ticket REL-311 was created to track the incident [E1].",
        evidence=mock_evidence,
        confidence=1.0,
        grounded=True,
        cited_evidence_ids=["E1"],
    )

    with patch("backend.api.routes.answer_question", return_value=mock_rag_response):
        res = client.post(
            "/api/ask",
            json={"question": "What happened with REL-311?", "retrieval_limit": 5},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["question"] == "What happened with REL-311?"
        assert "[E1]" in data["answer"]
        assert data["grounded"] is True
        assert len(data["evidence"]) == 1
        assert data["evidence"][0]["id"] == "E1"
        assert data["evidence"][0]["entity_name"] == "REL-311"
        assert data["cited_evidence_ids"] == ["E1"]


def test_ask_endpoint_ungrounded_invalid_citation(client: TestClient) -> None:
    mock_evidence = [
        EvidenceItem(
            message_id=8537794879600693670,
            document_id="doc_beta",
            entity_name="REL-311",
            statement="Support ticket REL-311 has been created.",
            statement_type="fact",
            relationship="ABOUT",
            match_type="exact_entity",
        )
    ]

    mock_rag_response = AnswerResponse(
        question="What happened with REL-311?",
        answer="Support ticket REL-311 was created [E99].",  # Invalid citation
        evidence=mock_evidence,
        confidence=0.5,
        grounded=False,
        cited_evidence_ids=[],
    )

    with patch("backend.api.routes.answer_question", return_value=mock_rag_response):
        res = client.post(
            "/api/ask",
            json={"question": "What happened with REL-311?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is False
        assert data["cited_evidence_ids"] == []


def test_ask_endpoint_ungrounded_no_citations(client: TestClient) -> None:
    mock_evidence = [
        EvidenceItem(
            message_id=8537794879600693670,
            document_id="doc_beta",
            entity_name="REL-311",
            statement="Support ticket REL-311 has been created.",
            statement_type="fact",
            relationship="ABOUT",
            match_type="exact_entity",
        )
    ]

    mock_rag_response = AnswerResponse(
        question="What happened with REL-311?",
        answer="Support ticket REL-311 was created without any evidence citations.",
        evidence=mock_evidence,
        confidence=0.5,
        grounded=False,
        cited_evidence_ids=[],
    )

    with patch("backend.api.routes.answer_question", return_value=mock_rag_response):
        res = client.post(
            "/api/ask",
            json={"question": "What happened with REL-311?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is False
        assert data["cited_evidence_ids"] == []


def test_ask_endpoint_offline_generator_fallback(client: TestClient) -> None:
    mock_evidence = [
        EvidenceItem(
            message_id=8537794879600693670,
            document_id="doc_beta",
            entity_name="REL-311",
            statement="Support ticket REL-311 has been created.",
            statement_type="fact",
            relationship="ABOUT",
            match_type="exact_entity",
        )
    ]

    mock_rag_response = AnswerResponse(
        question="What happened with REL-311?",
        answer="Gemini answer generator is not available (e.g. missing API key or client config).",
        evidence=mock_evidence,
        confidence=0.0,
        grounded=False,
        error="Generator init error: No API key was provided.",
    )

    with patch("backend.api.routes.answer_question", return_value=mock_rag_response):
        res = client.post(
            "/api/ask",
            json={"question": "What happened with REL-311?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is False
        assert len(data["evidence"]) == 1
        assert data["evidence"][0]["entity_name"] == "REL-311"
        assert data["cited_evidence_ids"] == []


def test_ask_endpoint_insufficient_evidence(client: TestClient) -> None:
    mock_rag_response = AnswerResponse(
        question="Who approved the budget?",
        answer="The available evidence is insufficient to answer this question.",
        evidence=[],
        confidence=1.0,
        grounded=True,
        cited_evidence_ids=[],
    )

    with patch("backend.api.routes.answer_question", return_value=mock_rag_response):
        res = client.post(
            "/api/ask",
            json={"question": "Who approved the budget?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["grounded"] is True
        assert "insufficient" in data["answer"].lower()
        assert data["evidence"] == []


def test_ask_endpoint_empty_and_whitespace_question(client: TestClient) -> None:
    res1 = client.post("/api/ask", json={"question": ""})
    assert res1.status_code == 422

    res2 = client.post("/api/ask", json={"question": "   "})
    assert res2.status_code == 422


# ===========================================================================
# Step 11: Dependency Tracing Endpoint Tests
# ===========================================================================


def test_trace_entities_endpoint(client: TestClient) -> None:
    mock_tracer = MagicMock()
    mock_tracer.get_available_entities.return_value = ["REL-311", "kernel-selector", "api-search"]

    with patch("backend.api.routes.get_active_tracer", return_value=mock_tracer):
        res = client.get("/api/trace/entities")
        assert res.status_code == 200
        data = res.json()
        assert data["total_count"] == 3
        assert data["entities"] == ["REL-311", "kernel-selector", "api-search"]


def test_trace_dependencies_endpoint_success(client: TestClient) -> None:
    mock_summary = TraceImpactSummary(
        root_entity="REL-311",
        traversal_depth=2,
        total_linked_entities=2,
        total_statements=2,
        statements_by_type={"fact": 1, "action": 1},
        affected_components=["api-search", "v3.1.1-legacy-tokenizer"],
        affected_messages=[8537794879600693670],
        affected_documents=["doc_beta"],
    )

    mock_trace_res = DependencyTraceResponse(
        root_entity="REL-311",
        found=True,
        impact_summary=mock_summary,
        timeline=[
            StatementTimelineItem(
                order_index=1,
                message_id=8537794879600693670,
                document_id="doc_beta",
                statement_type="fact",
                statement="Support ticket REL-311 has been created.",
                associated_entity="REL-311",
                relationship="ABOUT",
            )
        ],
        dependency_hops=[
            TraceHop(
                source_entity="REL-311",
                target_entity="api-search",
                hop_distance=1,
                via_message_id=8537794879600693670,
                document_id="doc_beta",
                relationship="CO_OCCURS_IN_MESSAGE",
                statements=["[fact] Support ticket REL-311 has been created."],
            )
        ],
        raw_evidence=[],
        error=None,
    )

    mock_tracer = MagicMock()
    mock_tracer.trace.return_value = mock_trace_res

    with patch("backend.api.routes.get_active_tracer", return_value=mock_tracer):
        res = client.post("/api/trace", json={"entity": "REL-311", "max_depth": 2})
        assert res.status_code == 200
        data = res.json()
        assert data["found"] is True
        assert data["root_entity"] == "REL-311"
        assert data["impact_summary"]["total_linked_entities"] == 2
        assert len(data["timeline"]) == 1
        assert len(data["dependency_hops"]) == 1


def test_trace_dependencies_endpoint_empty_entity(client: TestClient) -> None:
    res1 = client.post("/api/trace", json={"entity": ""})
    assert res1.status_code == 422

    res2 = client.post("/api/trace", json={"entity": "   "})
    assert res2.status_code == 422


def test_frontend_serving(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "Veridex" in res.text or "DeTrace" in res.text


def test_demo_queries_endpoint(client: TestClient) -> None:
    res = client.get("/api/demo/queries")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    assert any("REL-311" in q["query"] for q in data)


def test_evaluation_endpoint(client: TestClient) -> None:
    from backend.evaluation.models import EvaluationReport, ProvenanceCheckResult

    mock_report = EvaluationReport(
        total_queries=2,
        successful_queries=2,
        total_evidence_retrieved=4,
        total_hops_traversed=2,
        provenance_integrity=ProvenanceCheckResult(
            total_items_checked=6,
            valid_items=6,
            missing_message_ids=0,
            missing_document_ids=0,
            is_valid=True,
        ),
        average_retrieval_latency_ms=12.5,
        average_trace_latency_ms=15.2,
        hydradb_status="ONLINE",
    )

    mock_runner = MagicMock()
    mock_runner.run_evaluation.return_value = mock_report

    with patch("backend.evaluation.evaluation_runner.EvaluationRunner", return_value=mock_runner):
        res = client.get("/api/evaluation")
        assert res.status_code == 200
        data = res.json()
        assert data["total_queries"] == 2
        assert data["provenance_integrity"]["is_valid"] is True
        assert data["hydradb_status"] == "ONLINE"


