"""
Data models for HydraDB Deterministic Retrieval Layer & Dependency Tracer (Step 7 / Step 11).
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Retrieval query request model."""

    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query string cannot be empty or whitespace only.")
        return v


class EvidenceItem(BaseModel):
    """Structured evidence item retrieved from the HydraDB semantic graph."""

    message_id: int = Field(ge=0)
    document_id: str = Field(default="")
    entity_name: str | None = None
    entity_type: str | None = None
    statement: str | None = None
    statement_type: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    relationship: str | None = None
    source: str = "hydradb"
    match_type: str = "exact"  # exact_entity | exact_statement | partial_entity | partial_statement


class RetrievalResponse(BaseModel):
    """Structured response containing retrieved evidence items."""

    query: str
    results: list[EvidenceItem] = Field(default_factory=list)
    result_count: int = 0


# ===========================================================================
# Step 11: Dependency Tracing & Impact Analysis Models
# ===========================================================================


class DependencyTraceRequest(BaseModel):
    """Request model for tracing cross-team dependencies and impact paths."""

    entity: str = Field(min_length=1)
    max_depth: int = Field(default=2, ge=1, le=5)
    limit: int = Field(default=20, ge=1, le=100)

    @field_validator("entity")
    @classmethod
    def validate_entity(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Target entity cannot be empty or whitespace only.")
        return v


class TraceHop(BaseModel):
    """A single directional or co-occurrence hop in a dependency path."""

    source_entity: str
    target_entity: str
    hop_distance: int = Field(ge=1)
    via_message_id: int = Field(ge=0)
    document_id: str = Field(default="")
    relationship: str = "CO_OCCURS_IN_MESSAGE"
    statements: list[str] = Field(default_factory=list)


class StatementTimelineItem(BaseModel):
    """A chronological statement in the dependency trace timeline."""

    order_index: int = Field(ge=1)
    message_id: int = Field(ge=0)
    document_id: str = Field(default="")
    statement_type: str = "fact"
    statement: str
    associated_entity: str
    relationship: str = "ABOUT"


class TraceImpactSummary(BaseModel):
    """Aggregated impact metrics for the queried dependency graph."""

    root_entity: str
    traversal_depth: int = 0
    total_linked_entities: int = 0
    total_statements: int = 0
    statements_by_type: dict[str, int] = Field(default_factory=dict)
    affected_components: list[str] = Field(default_factory=list)
    affected_messages: list[int] = Field(default_factory=list)
    affected_documents: list[str] = Field(default_factory=list)
    authors: list[str] = Field(default_factory=list)
    teams: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)


class DependencyTraceResponse(BaseModel):
    """Structured response representing multi-hop dependency trace and impact."""

    root_entity: str
    found: bool = True
    impact_summary: TraceImpactSummary
    timeline: list[StatementTimelineItem] = Field(default_factory=list)
    dependency_hops: list[TraceHop] = Field(default_factory=list)
    raw_evidence: list[EvidenceItem] = Field(default_factory=list)
    error: str | None = None


# ===========================================================================
# Step 18: Temporal "Time-Travel" Graph & Incident Timeline Models
# ===========================================================================


class TimelineEvent(BaseModel):
    """A chronological event in an incident timeline with provenance and stage."""

    id: str
    order: int = Field(ge=1)
    timestamp: str | None = None
    relative_time: str = "+0m"
    source: str = "slack"  # slack | linear | github | system
    source_id: str = ""
    document_id: str = ""
    title: str = ""
    author: str | None = None
    channel_or_repo: str | None = None
    content_snippet: str = ""
    phase: str = "detection"  # detection | investigation | mitigation | resolution
    phase_label: str = "Detection"
    entities: list[str] = Field(default_factory=list)
    active_node_ids: list[str] = Field(default_factory=list)
    new_edges: list[dict[str, Any]] = Field(default_factory=list)


class TimelineGraphNode(BaseModel):
    """Graph node in the temporal graph state."""

    id: str
    label: str
    type: str = "component"  # component | incident | ticket | pr | channel | person
    source: str = "system"
    introduced_at_step: int = 1


class TimelineGraphEdge(BaseModel):
    """Directional edge formed in the temporal knowledge graph."""

    id: str
    source: str
    target: str
    label: str = "CONNECTED_TO"
    introduced_at_step: int = 1


class TemporalTimelineResponse(BaseModel):
    """Full temporal incident timeline and step-by-step graph evolution."""

    target_entity: str
    found: bool = True
    total_events: int = 0
    earliest_timestamp: str | None = None
    latest_timestamp: str | None = None
    duration_formatted: str = ""
    phase_counts: dict[str, int] = Field(default_factory=dict)
    events: list[TimelineEvent] = Field(default_factory=list)
    all_nodes: list[TimelineGraphNode] = Field(default_factory=list)
    all_edges: list[TimelineGraphEdge] = Field(default_factory=list)
    error: str | None = None

