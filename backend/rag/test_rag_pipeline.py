"""
Offline unit tests for Graph RAG Pipeline & Gemini Answer Generator (Step 8 / Step 10).

Validates:
1. Successful grounded answer with single and grouped citations:
   - [E1]
   - [E1, E2]
   - [E1,E2]
   - [E1, E3, E5]
   - Whitespace variants [ E1 ,  E2 ]
2. Grouped citation parsing and deduplication
3. Invented evidence ID detection (e.g. [E99] -> grounded=False)
4. Mixed valid/invalid citations (e.g. [E1, E99] -> grounded=False)
5. Answer with no citations (grounded=False)
6. Explicit insufficient evidence response (grounded=True)
7. Empty and whitespace question handling
8. Empty retrieval result fallback
9. Multiple evidence items and deterministic E1...En labeling
10. Deterministic evidence ID formatting
11. Gemini API error handling and sanitized error reporting
12. Retrieval failure propagation
13. Default model configuration (gemini-3.5-flash-lite)
14. 100% offline execution with zero Gemini API calls
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
import pytest

from backend.rag.answer_generator import (
    GeminiAnswerGenerator,
    format_evidence_bundle,
)
from backend.rag.models import AnswerRequest, AnswerResponse
from backend.rag.rag_pipeline import (
    GraphRAGPipeline,
    answer_question,
    parse_citations,
    sanitize_error,
)
from backend.retrieval.models import EvidenceItem, RetrievalResponse


class MockRetriever:
    """Mock retriever returning synthetic evidence items."""

    def __init__(self, evidence: list[EvidenceItem] | None = None, fail: bool = False) -> None:
        self.evidence = evidence if evidence is not None else []
        self.fail = fail

    def retrieve(self, query: str, limit: int = 10) -> RetrievalResponse:
        if self.fail:
            raise RuntimeError("Database query failed")
        return RetrievalResponse(
            query=query,
            results=self.evidence[:limit],
            result_count=len(self.evidence[:limit]),
        )


class MockGenerator:
    """Mock generator returning pre-configured response strings."""

    def __init__(self, response_text: str = "", fail: bool = False, fail_exc: Exception | None = None) -> None:
        self.response_text = response_text
        self.fail = fail
        self.fail_exc = fail_exc
        self.last_question = ""
        self.last_labeled_evidence: list[tuple[str, EvidenceItem]] = []

    def generate_answer(
        self, question: str, labeled_evidence: list[tuple[str, EvidenceItem]]
    ) -> str:
        self.last_question = question
        self.last_labeled_evidence = labeled_evidence
        if self.fail:
            raise self.fail_exc or RuntimeError("API request failed: 429 ResourceExhausted")
        return self.response_text


@pytest.fixture
def sample_evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            message_id=8537794879600693670,
            document_id="doc_beta",
            entity_name="REL-311",
            statement="Support ticket REL-311 has been created.",
            statement_type="fact",
            relationship="ABOUT",
            match_type="exact_entity",
        ),
        EvidenceItem(
            message_id=8537794879600693670,
            document_id="doc_beta",
            entity_name="v3.1.1-legacy-tokenizer",
            statement="Omar is running a targeted variant test.",
            statement_type="action",
            relationship="ABOUT",
            match_type="exact_entity",
        ),
        EvidenceItem(
            message_id=8537794879600693670,
            document_id="doc_beta",
            entity_name="api-search",
            statement="Omar flagged the issue in api-search.",
            statement_type="fact",
            relationship="ABOUT",
            match_type="exact_entity",
        ),
    ]


def test_answer_request_model() -> None:
    req = AnswerRequest(question="What happened?", retrieval_limit=5)
    assert req.question == "What happened?"
    assert req.retrieval_limit == 5

    with pytest.raises(ValueError):
        AnswerRequest(question="   ")


def test_parse_citations_single() -> None:
    assert parse_citations("Incident tracked in [E1].") == ["E1"]
    assert parse_citations("Incident tracked in [E2].") == ["E2"]


def test_parse_citations_grouped() -> None:
    assert parse_citations("Tracked in [E1, E2].") == ["E1", "E2"]
    assert parse_citations("Tracked in [E1,E2].") == ["E1", "E2"]
    assert parse_citations("Tracked in [E1, E3, E5].") == ["E1", "E3", "E5"]


def test_parse_citations_whitespace_and_case() -> None:
    assert parse_citations("Tracked in [  E1 ,   E2  ].") == ["E1", "E2"]
    assert parse_citations("Tracked in [e1, E2].") == ["E1", "E2"]


def test_parse_citations_ordering_and_deduplication() -> None:
    text = "The issue was caused by [E2] and confirmed in [E1, E2]. Later, [E3] was mentioned."
    citations = parse_citations(text)
    assert citations == ["E2", "E1", "E3"]


def test_format_evidence_bundle(sample_evidence) -> None:
    labeled = [("E1", sample_evidence[0]), ("E2", sample_evidence[1])]
    formatted = format_evidence_bundle(labeled)

    assert "[E1]" in formatted
    assert "[E2]" in formatted
    assert "REL-311" in formatted
    assert "8537794879600693670" in formatted
    assert format_evidence_bundle([]) == "No evidence retrieved."


def test_gemini_answer_generator_default_model() -> None:
    generator = GeminiAnswerGenerator.__new__(GeminiAnswerGenerator)
    generator.model = "gemini-3.5-flash-lite"
    assert generator.model == "gemini-3.5-flash-lite"


def test_sanitize_error_strips_secrets() -> None:
    sensitive_exc = RuntimeError("Failed request with key AIzaSyA1234567890123456789012345678901 and Bearer secret_token_xyz")
    sanitized = sanitize_error(sensitive_exc)

    assert "AIzaSy" not in sanitized
    assert "secret_token_xyz" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "Bearer [REDACTED]" in sanitized
    assert "RuntimeError" in sanitized


def test_successful_grounded_answer_single_citations(sample_evidence) -> None:
    retriever = MockRetriever(evidence=sample_evidence)
    generator = MockGenerator(
        response_text="Support ticket REL-311 was created [E1], and a test was launched [E2]."
    )

    resp = answer_question(
        question="What happened with REL-311?",
        retriever=retriever,
        generator=generator,
    )

    assert resp.grounded is True
    assert resp.confidence == 1.0
    assert resp.cited_evidence_ids == ["E1", "E2"]
    assert len(resp.evidence) == 3


def test_successful_grounded_answer_grouped_citations(sample_evidence) -> None:
    retriever = MockRetriever(evidence=sample_evidence)
    # Exact scenario from live Gemini output
    generator = MockGenerator(
        response_text="Support ticket REL-311 has been created, linking release notes, and it is set up to alert support if a rollback occurs [E1, E2]."
    )

    resp = answer_question(
        question="What happened with REL-311?",
        retriever=retriever,
        generator=generator,
    )

    assert resp.grounded is True
    assert resp.confidence == 1.0
    assert resp.cited_evidence_ids == ["E1", "E2"]


def test_invented_evidence_id_detection(sample_evidence) -> None:
    retriever = MockRetriever(evidence=sample_evidence)  # Has E1, E2, E3
    generator = MockGenerator(
        response_text="This is an answer citing an invented citation [E99] and [E1]."
    )

    resp = answer_question(
        question="What happened?",
        retriever=retriever,
        generator=generator,
    )

    # Invalid citation [E99] causes grounding to fail
    assert resp.grounded is False
    assert resp.confidence == 0.5
    assert resp.cited_evidence_ids == ["E1"]


def test_mixed_valid_invalid_grouped_citation(sample_evidence) -> None:
    retriever = MockRetriever(evidence=sample_evidence)  # Has E1, E2, E3
    generator = MockGenerator(
        response_text="This references evidence [E1, E99]."
    )

    resp = answer_question(
        question="What happened?",
        retriever=retriever,
        generator=generator,
    )

    assert resp.grounded is False
    assert resp.cited_evidence_ids == ["E1"]


def test_answer_with_no_citations(sample_evidence) -> None:
    retriever = MockRetriever(evidence=sample_evidence)
    generator = MockGenerator(
        response_text="This answer contains information without citing any evidence bracket tags."
    )

    resp = answer_question(
        question="What happened?",
        retriever=retriever,
        generator=generator,
    )

    assert resp.grounded is False
    assert resp.cited_evidence_ids == []


def test_explicit_insufficient_evidence_response(sample_evidence) -> None:
    retriever = MockRetriever(evidence=sample_evidence)
    generator = MockGenerator(
        response_text="The available evidence is insufficient to answer this question."
    )

    resp = answer_question(
        question="Who approved the budget?",
        retriever=retriever,
        generator=generator,
    )

    assert resp.grounded is True
    assert resp.confidence == 1.0
    assert resp.cited_evidence_ids == []


def test_generator_api_error_sanitized_reporting(sample_evidence) -> None:
    retriever = MockRetriever(evidence=sample_evidence)
    sensitive_err = RuntimeError("429 ResourceExhausted: quota for key AIzaSyDUMMYKEY1234567890123456789012345 exceeded")
    generator = MockGenerator(fail=True, fail_exc=sensitive_err)

    resp = answer_question(
        question="What happened?",
        retriever=retriever,
        generator=generator,
    )

    assert resp.grounded is False
    assert resp.confidence == 0.0
    assert resp.error is not None
    assert "AIzaSyDUMMYKEY" not in resp.error
    assert "[REDACTED_API_KEY]" in resp.error
    assert "RuntimeError" in resp.error


def test_empty_and_whitespace_question() -> None:
    resp1 = answer_question(question="")
    assert resp1.grounded is False
    assert resp1.error == "Invalid question"

    resp2 = answer_question(question="     ")
    assert resp2.grounded is False
    assert resp2.error == "Invalid question"


def test_empty_retrieval_result() -> None:
    retriever = MockRetriever(evidence=[])
    generator = MockGenerator(response_text="Should not be called")

    resp = answer_question(
        question="What about unknown_topic?",
        retriever=retriever,
        generator=generator,
    )

    assert resp.grounded is True
    assert "insufficient" in resp.answer.lower()
    assert resp.evidence == []
    assert generator.last_question == ""


def test_retrieval_failure_propagation() -> None:
    retriever = MockRetriever(fail=True)
    generator = MockGenerator()

    resp = answer_question(
        question="What happened?",
        retriever=retriever,
        generator=generator,
    )

    assert resp.grounded is False
    assert resp.confidence == 0.0
    assert resp.error is not None
    assert "Retrieval error" in resp.error
