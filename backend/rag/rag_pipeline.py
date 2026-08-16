"""
Graph RAG Pipeline (Step 8 / Step 10).

Coordinates deterministic HydraDB retrieval, evidence labeling [E1, E2, ...],
Gemini Interactions API answer generation, and strict citation/grounding verification.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Protocol

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.rag.answer_generator import GeminiAnswerGenerator
    from backend.rag.models import AnswerRequest, AnswerResponse
    from backend.retrieval.hydra_retriever import HydraRetriever
    from backend.retrieval.models import EvidenceItem, RetrievalResponse
except ImportError:
    from answer_generator import GeminiAnswerGenerator  # type: ignore[no-redef]
    from models import AnswerRequest, AnswerResponse  # type: ignore[no-redef]
    from hydra_retriever import HydraRetriever  # type: ignore[no-redef]
    from models import EvidenceItem, RetrievalResponse  # type: ignore[no-redef]


class RetrieverProtocol(Protocol):
    def retrieve(self, query: str, limit: int = 10) -> RetrievalResponse: ...


class GeneratorProtocol(Protocol):
    def generate_answer(
        self, question: str, labeled_evidence: list[tuple[str, EvidenceItem]]
    ) -> str: ...


def sanitize_error(exc: Exception) -> str:
    """
    Sanitize error message to report safe diagnostic information without leaking secrets.
    """
    exc_type = type(exc).__name__
    raw_msg = str(exc)

    # Extract status code if available
    status_code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    status_str = f" [status={status_code}]" if status_code is not None else ""

    # Sanitize API keys and bearer tokens
    sanitized = re.sub(r"AIza[0-9A-Za-z\-_]{25,}", "[REDACTED_API_KEY]", raw_msg)
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", sanitized)
    sanitized = re.sub(r"key=[A-Za-z0-9_\-]+", "key=[REDACTED]", sanitized)
    sanitized = re.sub(r"token=[A-Za-z0-9_\-]+", "token=[REDACTED]", sanitized)


    return f"{exc_type}{status_str}: {sanitized}"


def parse_citations(text: str) -> list[str]:
    """
    Extract all E# citation tags from generated text in order of appearance.
    Supports single [E1], [E2] and grouped citations like [E1, E2], [E1,E2], [E1, E3, E5].
    """
    if not text:
        return []

    seen: set[str] = set()
    ordered: list[str] = []

    # Find all bracketed contents e.g. [E1, E2], [E1]
    bracket_pattern = re.compile(r"\[(.*?)\]")
    for match in bracket_pattern.finditer(text):
        bracket_content = match.group(1)
        # Extract all E# references inside the bracket group
        e_matches = re.findall(r"\bE(\d+)\b", bracket_content, re.IGNORECASE)
        for num in e_matches:
            tag = f"E{int(num)}"
            if tag not in seen:
                seen.add(tag)
                ordered.append(tag)

    return ordered



class GraphRAGPipeline:
    """
    End-to-end Graph RAG pipeline combining HydraDB deterministic retrieval and Gemini generation.
    """

    def __init__(
        self,
        retriever: RetrieverProtocol | None = None,
        generator: GeneratorProtocol | None = None,
    ) -> None:
        self.retriever = retriever or HydraRetriever()
        self.generator = generator

    def answer_question(
        self,
        question: str,
        retrieval_limit: int = 10,
    ) -> AnswerResponse:
        """
        Answer a user question using deterministic graph evidence and grounded LLM generation.
        """
        # 1. Validate question
        if not isinstance(question, str) or not question.strip():
            return AnswerResponse(
                question=str(question or ""),
                answer="Question cannot be empty or whitespace only.",
                evidence=[],
                confidence=0.0,
                grounded=False,
                error="Invalid question",
            )

        clean_question = question.strip()

        # 2. Retrieve evidence from HydraDB
        try:
            retrieval_res = self.retriever.retrieve(query=clean_question, limit=retrieval_limit)
            raw_evidence = retrieval_res.results
        except Exception as exc:
            sanitized = sanitize_error(exc)
            return AnswerResponse(
                question=clean_question,
                answer="Failed to retrieve evidence from HydraDB graph.",
                evidence=[],
                confidence=0.0,
                grounded=False,
                error=f"Retrieval error: {sanitized}",
            )

        # 3. Label evidence deterministically [E1, E2, ...]
        labeled_evidence: list[tuple[str, EvidenceItem]] = [
            (f"E{idx}", item) for idx, item in enumerate(raw_evidence, start=1)
        ]
        valid_labels = {f"E{idx}" for idx in range(1, len(raw_evidence) + 1)}

        # 4. Handle empty retrieval result
        if not labeled_evidence:
            return AnswerResponse(
                question=clean_question,
                answer="The available evidence is insufficient to answer this question.",
                evidence=[],
                confidence=1.0,
                grounded=True,
                cited_evidence_ids=[],
            )

        # 5. Initialize generator if needed
        generator = self.generator
        if generator is None:
            try:
                generator = GeminiAnswerGenerator()
            except Exception as exc:
                sanitized = sanitize_error(exc)
                return AnswerResponse(
                    question=clean_question,
                    answer="Gemini answer generator is not available (e.g. missing API key or client config).",
                    evidence=raw_evidence,
                    confidence=0.0,
                    grounded=False,
                    error=f"Generator init error: {sanitized}",
                )

        # 6. Generate answer
        try:
            raw_answer = generator.generate_answer(
                question=clean_question,
                labeled_evidence=labeled_evidence,
            )
        except Exception as exc:
            sanitized = sanitize_error(exc)
            return AnswerResponse(
                question=clean_question,
                answer="Failed to generate answer from model.",
                evidence=raw_evidence,
                confidence=0.0,
                grounded=False,
                error=f"Model generation error: {sanitized}",
            )

        # 7. Parse and validate citations
        cited_ids = parse_citations(raw_answer)
        invalid_citations = [c for c in cited_ids if c not in valid_labels]
        valid_cited_ids = [c for c in cited_ids if c in valid_labels]

        is_insufficient_statement = (
            "evidence is insufficient" in raw_answer.lower()
            or "insufficient evidence" in raw_answer.lower()
        )

        if invalid_citations:
            grounded = False
        elif is_insufficient_statement:
            grounded = True
        elif valid_cited_ids:
            grounded = True
        else:
            grounded = False

        confidence = 1.0 if grounded else 0.5

        return AnswerResponse(
            question=clean_question,
            answer=raw_answer,
            evidence=raw_evidence,
            confidence=confidence,
            grounded=grounded,
            cited_evidence_ids=valid_cited_ids,
        )


def answer_question(
    question: str,
    retrieval_limit: int = 10,
    retriever: RetrieverProtocol | None = None,
    generator: GeneratorProtocol | None = None,
) -> AnswerResponse:
    """Convenience function to run the Graph RAG pipeline."""
    pipeline = GraphRAGPipeline(retriever=retriever, generator=generator)
    return pipeline.answer_question(question=question, retrieval_limit=retrieval_limit)
