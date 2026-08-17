"""
Data models for HydraDB Evaluation, Provenance Invariants, and Ablation Benchmarking (Step 12).
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class ProvenanceCheckResult(BaseModel):
    """Integrity check result for source message and document provenance."""

    total_items_checked: int = 0
    valid_items: int = 0
    missing_message_ids: int = 0
    missing_document_ids: int = 0
    invalid_citations: int = 0
    is_valid: bool = True
    errors: list[str] = Field(default_factory=list)


class AblationComparisonItem(BaseModel):
    """Comparison between Graph-based Retrieval and Naive Text Matching."""

    query: str
    graph_evidence_count: int
    graph_entities_found: list[str]
    graph_relationships_found: list[str]
    graph_provenance_valid: bool
    text_matches_count: int
    text_has_graph_relationships: bool
    text_has_typed_statements: bool
    structural_advantage_summary: str


class EvaluationResultItem(BaseModel):
    """Result of running a benchmark query through the deterministic retrieval & trace layer."""

    query: str
    target_entity: str | None = None
    evidence_count: int = 0
    matched_entities: list[str] = Field(default_factory=list)
    matched_statement_types: dict[str, int] = Field(default_factory=dict)
    relationships_discovered: list[str] = Field(default_factory=list)
    source_message_ids: list[int] = Field(default_factory=list)
    source_document_ids: list[str] = Field(default_factory=list)
    dependency_path_count: int = 0
    linked_components: list[str] = Field(default_factory=list)
    provenance_valid: bool = True
    retrieval_latency_ms: float = 0.0
    trace_latency_ms: float = 0.0


class EvaluationReport(BaseModel):
    """Comprehensive evaluation report for HydraDB Hackathon Track 1."""

    total_queries: int = 0
    successful_queries: int = 0
    total_evidence_retrieved: int = 0
    total_hops_traversed: int = 0
    provenance_integrity: ProvenanceCheckResult
    query_results: list[EvaluationResultItem] = Field(default_factory=list)
    ablation_comparisons: list[AblationComparisonItem] = Field(default_factory=list)
    average_retrieval_latency_ms: float = 0.0
    average_trace_latency_ms: float = 0.0
    hydradb_status: str = "ONLINE"
