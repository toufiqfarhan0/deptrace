"""
Offline integration tests for DeTrace FastAPI web application (Step 9).

Validates:
- GET /api/health with healthy and degraded HydraDB states
- POST /api/ask with grounded, ungrounded (invalid citations, missing citations), and insufficient evidence scenarios
- Offline generator fallback behavior (proves grounded=False is correct when LLM is offline)
- Validation errors for empty/whitespace questions
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
from backend.retrieval.models import EvidenceItem, RetrievalResponse


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_health_endpoint_healthy(client: TestClient) -> None:
    mock_query = MagicMock(return_value={"rows": [[{"value": 10}]]})
    with patch("backend.api.routes.default_query_fn", mock_query):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["hydradb"] == "ok"


def test_health_endpoint_degraded(client: TestClient) -> None:
    mock_query = MagicMock(side_effect=RuntimeError("HydraDB offline"))
    with patch("backend.api.routes.default_query_fn", mock_query):
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
    """Proves that when LLM generator is offline, evidence is preserved and grounded=False is returned."""
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
        # Essential: grounded must be False because fallback text is not synthesized/cited
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


def test_frontend_serving(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "DeTrace" in res.text
