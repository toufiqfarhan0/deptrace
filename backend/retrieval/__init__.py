"""
HydraDB Retrieval & Dependency Tracing Package (Step 7 / Step 11).

Provides deterministic graph-based retrieval and multi-hop dependency tracing over HydraDB.
"""

from __future__ import annotations

from backend.retrieval.dependency_tracer import DependencyTracer
from backend.retrieval.hydra_retriever import HydraRetriever, retrieve
from backend.retrieval.models import (
    DependencyTraceRequest,
    DependencyTraceResponse,
    EvidenceItem,
    QueryRequest,
    RetrievalResponse,
    StatementTimelineItem,
    TraceHop,
    TraceImpactSummary,
)

__all__ = [
    "DependencyTraceRequest",
    "DependencyTraceResponse",
    "DependencyTracer",
    "EvidenceItem",
    "HydraRetriever",
    "QueryRequest",
    "RetrievalResponse",
    "StatementTimelineItem",
    "TraceHop",
    "TraceImpactSummary",
    "retrieve",
]
