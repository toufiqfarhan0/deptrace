"""
HydraDB Retrieval & Driver Factory (Step 17D).

Provides factory functions to dynamically instantiate the appropriate retrieval,
tracing, and health-check drivers based on HYDRA_MODE ('local' vs 'cloud').
"""

from __future__ import annotations

from backend.config import AppConfig
from backend.retrieval.cloud_retriever import HydraCloudRetriever
from backend.retrieval.cloud_tracer import HydraCloudTracer
from backend.retrieval.dependency_tracer import DependencyTracer
from backend.retrieval.hydra_retriever import HydraRetriever
from backend.semantic.verify_semantic_graph import query as local_query_fn


def get_hydra_mode() -> str:
    """Return the active HydraDB driver mode: 'local' | 'cloud'."""
    return AppConfig.get_hydra_mode()


def get_active_retriever() -> Any:
    """Return the configured retriever instance based on HYDRA_MODE."""
    mode = get_hydra_mode()
    if mode == "cloud":
        return HydraCloudRetriever()
    return HydraRetriever()


def get_active_tracer() -> Any:
    """Return the configured dependency tracer instance based on HYDRA_MODE."""
    mode = get_hydra_mode()
    if mode == "cloud":
        return HydraCloudTracer()
    return DependencyTracer()


def check_active_health(query_fn: Callable[[str], dict[str, Any]] | None = None) -> dict[str, str]:
    """
    Execute health check against the active HydraDB driver.
    """
    mode = get_hydra_mode()
    if mode == "cloud":
        retriever = HydraCloudRetriever()
        res = retriever.check_health()
        return {
            "status": res.get("status", "degraded"),
            "hydradb": res.get("hydradb", "unknown"),
        }

    # Local OpenCypher health check
    q_fn = query_fn or local_query_fn
    try:
        res = q_fn("MATCH (m:Message) RETURN count(*) AS message_count LIMIT 1")
        if isinstance(res, dict) and "rows" in res:
            return {"status": "ok", "hydradb": "ok"}
        return {"status": "degraded", "hydradb": "unexpected_response"}
    except Exception as exc:
        return {"status": "degraded", "hydradb": f"unreachable: {type(exc).__name__}"}
