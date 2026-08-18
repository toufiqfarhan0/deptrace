"""
HydraDB Retrieval & Driver Factory.

Provides factory functions to instantiate the local HydraDB retrieval,
tracing, and health-check drivers.
"""

from __future__ import annotations

from typing import Any, Callable

from backend.config import AppConfig
from backend.retrieval.dependency_tracer import DependencyTracer
from backend.retrieval.hydra_retriever import HydraRetriever
from backend.semantic.verify_semantic_graph import query as local_query_fn


def get_hydra_mode() -> str:
    """Return the active HydraDB driver mode: 'local'."""
    return "local"


def get_active_retriever() -> HydraRetriever:
    """Return the configured local HydraRetriever instance."""
    return HydraRetriever()


def get_active_tracer() -> DependencyTracer:
    """Return the configured local DependencyTracer instance."""
    return DependencyTracer()


def check_active_health(query_fn: Callable[[str], dict[str, Any]] | None = None) -> dict[str, str]:
    """
    Execute health check against the local HydraDB driver.
    """
    q_fn = query_fn or local_query_fn
    try:
        res = q_fn("MATCH (m:Message) RETURN count(*) AS message_count LIMIT 1")
        if isinstance(res, dict) and "rows" in res:
            return {"status": "ok", "hydradb": "ok (local: default)"}
        return {"status": "degraded", "hydradb": "unexpected_response"}
    except Exception as exc:
        return {"status": "degraded", "hydradb": f"unreachable: {type(exc).__name__}"}
