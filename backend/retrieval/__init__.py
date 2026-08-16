"""
HydraDB Retrieval Package (Step 7).

Provides deterministic graph-based retrieval over HydraDB semantic graph.
"""

from __future__ import annotations

from backend.retrieval.hydra_retriever import HydraRetriever, retrieve
from backend.retrieval.models import (
    EvidenceItem,
    QueryRequest,
    RetrievalResponse,
)

__all__ = [
    "EvidenceItem",
    "HydraRetriever",
    "QueryRequest",
    "RetrievalResponse",
    "retrieve",
]
