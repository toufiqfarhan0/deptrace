"""
HTTP API routes for DeTrace Graph RAG & Dependency Tracing application (Step 9 / Step 11).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.rag_pipeline import answer_question
from backend.retrieval.dependency_tracer import DependencyTracer
from backend.retrieval.models import (
    DependencyTraceRequest,
    DependencyTraceResponse,
)
from backend.semantic.verify_semantic_graph import query as default_query_fn

router = APIRouter(prefix="/api", tags=["rag"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    hydradb: str


class AskRequest(BaseModel):
    """Ask question request payload."""

    question: str = Field(min_length=1)
    retrieval_limit: int = Field(default=10, ge=1, le=50)

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question string cannot be empty or whitespace only.")
        return v


class EvidenceResponseItem(BaseModel):
    """Structured evidence item for client presentation."""

    id: str
    message_id: int
    document_id: str
    entity_name: str | None = None
    entity_type: str | None = None
    statement: str | None = None
    statement_type: str | None = None
    relationship: str | None = None
    match_type: str = "exact"


class AskResponse(BaseModel):
    """Grounded question answering response payload."""

    question: str
    answer: str
    grounded: bool
    confidence: float | None = 1.0
    evidence: list[EvidenceResponseItem] = Field(default_factory=list)
    cited_evidence_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class EntityListResponse(BaseModel):
    """List of available entities present in the knowledge graph."""

    entities: list[str] = Field(default_factory=list)
    total_count: int = 0


@router.get("/health", response_model=HealthResponse)
def health_check(query_fn=None) -> HealthResponse:
    """
    Lightweight health check checking HydraDB graph connectivity.
    Does NOT invoke Gemini API.
    """
    q_fn = query_fn or default_query_fn
    try:
        res = q_fn("MATCH (m:Message) RETURN count(*) AS message_count LIMIT 1")
        if isinstance(res, dict) and "rows" in res:
            return HealthResponse(status="ok", hydradb="ok")
        return HealthResponse(status="degraded", hydradb="unexpected_response")
    except Exception as exc:
        return HealthResponse(status="degraded", hydradb=f"unreachable: {type(exc).__name__}")


@router.post("/ask", response_model=AskResponse)
def ask_question_endpoint(
    payload: AskRequest,
    retriever=None,
    generator=None,
) -> AskResponse:
    """
    Answer an enterprise question using deterministic HydraDB retrieval + grounded Gemini synthesis.
    """
    try:
        rag_res = answer_question(
            question=payload.question,
            retrieval_limit=payload.retrieval_limit,
            retriever=retriever,
            generator=generator,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal RAG pipeline error: {type(exc).__name__}",
        ) from exc

    # Format labeled evidence for presentation
    formatted_evidence: list[EvidenceResponseItem] = [
        EvidenceResponseItem(
            id=f"E{idx}",
            message_id=item.message_id,
            document_id=item.document_id,
            entity_name=item.entity_name,
            entity_type=item.entity_type,
            statement=item.statement,
            statement_type=item.statement_type,
            relationship=item.relationship,
            match_type=item.match_type,
        )
        for idx, item in enumerate(rag_res.evidence, start=1)
    ]

    return AskResponse(
        question=rag_res.question,
        answer=rag_res.answer,
        grounded=rag_res.grounded,
        confidence=rag_res.confidence,
        evidence=formatted_evidence,
        cited_evidence_ids=rag_res.cited_evidence_ids,
        error=rag_res.error,
    )


@router.get("/trace/entities", response_model=EntityListResponse)
def get_trace_entities_endpoint(tracer=None) -> EntityListResponse:
    """
    Get all unique entities in HydraDB available for dependency tracing.
    """
    dt = tracer or DependencyTracer()
    entities = dt.get_available_entities()
    return EntityListResponse(entities=entities, total_count=len(entities))


@router.post("/trace", response_model=DependencyTraceResponse)
def trace_dependencies_endpoint(
    payload: DependencyTraceRequest,
    tracer=None,
) -> DependencyTraceResponse:
    """
    Execute deterministic multi-hop dependency tracing starting from a target entity.
    """
    dt = tracer or DependencyTracer()
    try:
        res = dt.trace(
            entity=payload.entity,
            max_depth=payload.max_depth,
            limit=payload.limit,
        )
        return res
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dependency tracing error: {type(exc).__name__}",
        ) from exc


@router.get("/evaluation")
def get_evaluation_report_endpoint(runner=None) -> dict[str, Any]:
    """
    Run and return the deterministic HydraDB evaluation and ablation benchmark report.
    """
    try:
        from backend.evaluation.evaluation_runner import EvaluationRunner
        ev_runner = runner or EvaluationRunner()
        report = ev_runner.run_evaluation()
        return report.model_dump()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation runner error: {type(exc).__name__}",
        ) from exc


@router.get("/demo/queries")
def get_demo_queries_endpoint() -> list[dict[str, str]]:
    """
    Return pre-configured demo and evaluation investigation queries.
    """
    from backend.evaluation.evaluation_runner import BENCHMARK_QUERIES
    return BENCHMARK_QUERIES


