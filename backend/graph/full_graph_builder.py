"""
Full Knowledge Graph Topology Builder for Veridex Interactive Canvas Explorer.

Generates complete enterprise graph nodes and typed relationships across
Slack, Linear, GitHub, Jira, Confluence, and PagerDuty.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class GraphCanvasNode(BaseModel):
    id: str
    label: str
    type: str  # incident, pull_request, linear_issue, jira_ticket, confluence_rfc, service, component
    source: str  # slack, github, linear, jira, confluence, pagerduty
    title: str
    summary: str
    status: str  # resolved, active, merged, approved, open
    authority_score: float
    statements_count: int = 1
    statements: list[str] = Field(default_factory=list)
    initial_x: float = 0.0
    initial_y: float = 0.0


class GraphCanvasEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str  # CAUSED_BY, RESOLVES, REVERTS, DEPENDS_ON, STANDARDIZES, AFFECTS, SUPERSEDES, ABOUT
    label: str
    source_system: str
    statement: str
    document_id: str | None = None


class FullGraphResponse(BaseModel):
    nodes: list[GraphCanvasNode]
    edges: list[GraphCanvasEdge]
    total_nodes: int
    total_edges: int
    node_types: dict[str, int]
    relationship_types: dict[str, int]
    sources_breakdown: dict[str, int]


CANONICAL_CANVAS_NODES: list[dict[str, Any]] = [
    {
        "id": "INC-2026",
        "label": "INC-2026",
        "type": "incident",
        "source": "slack",
        "title": "P0 Outage: Runtime Pool Starvation",
        "summary": "GPU queue saturation caused by cgroup memory limit exhaustion.",
        "status": "resolved",
        "authority_score": 0.95,
        "statements": [
            "[action] SRE initiated emergency triage in #incidents channel.",
            "[fact] Memory pressure in kernel-selector triggered container evictions.",
            "[outcome] Resolved by emergency rollback hotfix PR-99501."
        ],
        "initial_x": 480.0,
        "initial_y": 280.0,
    },
    {
        "id": "PR-99501",
        "label": "PR-99501",
        "type": "pull_request",
        "source": "github",
        "title": "Emergency Revert & KMS Guardrail Hotfix",
        "summary": "Reverts v3.1.1 legacy tokenizer and enforces service-scoped KMS limits.",
        "status": "merged",
        "authority_score": 0.98,
        "statements": [
            "[decision] Merged commit d4f881a with service-scoped KMS guardrails.",
            "[action] Deployed hotfix to canary clusters within 42 minutes.",
            "[fact] Restored gateway p99 latency to baseline 32ms."
        ],
        "initial_x": 640.0,
        "initial_y": 180.0,
    },
    {
        "id": "REL-311",
        "label": "REL-311",
        "type": "linear_issue",
        "source": "linear",
        "title": "Tokenizer Fallback Regression Issue",
        "summary": "Deployment of legacy tokenizer triggered memory leaks and rate limits.",
        "status": "resolved",
        "authority_score": 0.88,
        "statements": [
            "[fact] Tokenizer fallback regression caused request timeout breaches.",
            "[decision] Marked as resolved after PR-99501 hotfix rollback."
        ],
        "initial_x": 320.0,
        "initial_y": 180.0,
    },
    {
        "id": "kernel-selector",
        "label": "kernel-selector",
        "type": "service",
        "source": "github",
        "title": "Core GPU Kernel Dispatch Service",
        "summary": "Low-level CUDA and ROCm dispatch daemon managing tensor batch queues.",
        "status": "active",
        "authority_score": 0.92,
        "statements": [
            "[fact] Kernel selector allocates shared memory cgroup partitions.",
            "[fact] Suffered OOM crashes during concurrent inference spikes."
        ],
        "initial_x": 480.0,
        "initial_y": 120.0,
    },
    {
        "id": "Bluecrest",
        "label": "Bluecrest",
        "type": "component",
        "source": "slack",
        "title": "Dedicated Tier Gateway (Bluecrest)",
        "summary": "Enterprise customer gateway experiencing 3x latency degradation.",
        "status": "resolved",
        "authority_score": 0.85,
        "statements": [
            "[fact] Bluecrest dedicated gateway observed 3x p99 latency spikes.",
            "[action] Rate-limiting relaxed after KMS partition isolation applied."
        ],
        "initial_x": 660.0,
        "initial_y": 380.0,
    },
    {
        "id": "api-search",
        "label": "api-search",
        "type": "service",
        "source": "github",
        "title": "High-Throughput Vector Search Gateway",
        "summary": "Search routing layer responsible for query dispatch.",
        "status": "active",
        "authority_score": 0.90,
        "statements": [
            "[fact] Ingests candidate vectors and routes semantic queries to cluster index."
        ],
        "initial_x": 240.0,
        "initial_y": 320.0,
    },
    {
        "id": "gpu-prod-pool-2",
        "label": "gpu-prod-pool-2",
        "type": "component",
        "source": "pagerduty",
        "title": "Production GPU Cluster Pool 2",
        "summary": "Primary H100 GPU compute cluster partition.",
        "status": "active",
        "authority_score": 0.90,
        "statements": [
            "[fact] Queue depth exceeded 85% safety threshold triggering Sev-1 pager."
        ],
        "initial_x": 340.0,
        "initial_y": 420.0,
    },
    {
        "id": "cgroup-manager",
        "label": "cgroup-manager",
        "type": "component",
        "source": "linear",
        "title": "Linux Cgroup Memory Guard",
        "summary": "Controls container swap limits and OOM killer policies.",
        "status": "active",
        "authority_score": 0.85,
        "statements": [
            "[fact] Enforces hard memory boundaries on runtime worker pools."
        ],
        "initial_x": 520.0,
        "initial_y": 440.0,
    },
    {
        "id": "JIRA-4029",
        "label": "JIRA-4029",
        "type": "jira_ticket",
        "source": "jira",
        "title": "Cross-Region KMS Key Sync Timeout",
        "summary": "Jira ticket tracking KMS multi-region key replication timeouts under high QPS.",
        "status": "resolved",
        "authority_score": 0.89,
        "statements": [
            "[fact] Cross-region KMS sync times out when downstream tokenizers breach 150ms.",
            "[action] Blocked Bluecrest migration until partition guardrails landed."
        ],
        "initial_x": 800.0,
        "initial_y": 260.0,
    },
    {
        "id": "RFC-881",
        "label": "RFC-881",
        "type": "confluence_rfc",
        "source": "confluence",
        "title": "RFC-881: Service-Scoped Key Isolation ADR",
        "summary": "Architectural Decision Record mandating tenant KMS isolation and namespace budgeting.",
        "status": "approved",
        "authority_score": 0.96,
        "statements": [
            "[decision] Architecture committee approved strict partition namespace limits.",
            "[fact] Standardizes security policy implemented in PR-99501 and JIRA-4029."
        ],
        "initial_x": 800.0,
        "initial_y": 120.0,
    },
    {
        "id": "ENG-68910",
        "label": "ENG-68910",
        "type": "linear_issue",
        "source": "linear",
        "title": "Cgroup Limit Calibration Task",
        "summary": "Recalibrates worker swap thresholds to prevent OOM evictions.",
        "status": "resolved",
        "authority_score": 0.86,
        "statements": [
            "[action] Updated container limits from 8GB to 16GB dedicated swap."
        ],
        "initial_x": 160.0,
        "initial_y": 440.0,
    },
    {
        "id": "ENG-30521",
        "label": "ENG-30521",
        "type": "linear_issue",
        "source": "linear",
        "title": "Tokenizer Fallback Interop Task",
        "summary": "Engineering task to audit legacy tokenizer compatibility.",
        "status": "resolved",
        "authority_score": 0.84,
        "statements": [
            "[fact] Documented fallback latency budget constraints."
        ],
        "initial_x": 180.0,
        "initial_y": 180.0,
    },
]

CANONICAL_CANVAS_EDGES: list[dict[str, Any]] = [
    {
        "id": "e1",
        "source": "INC-2026",
        "target": "kernel-selector",
        "type": "CAUSED_BY",
        "label": "CAUSED_BY",
        "source_system": "slack",
        "statement": "Kernel-selector memory exhaustion triggered INC-2026 emergency pool starvation.",
    },
    {
        "id": "e2",
        "source": "INC-2026",
        "target": "gpu-prod-pool-2",
        "type": "AFFECTS",
        "label": "AFFECTS",
        "source_system": "pagerduty",
        "statement": "Incident caused queue depth in gpu-prod-pool-2 to exceed 85% capacity.",
    },
    {
        "id": "e3",
        "source": "INC-2026",
        "target": "Bluecrest",
        "type": "AFFECTS",
        "label": "AFFECTS",
        "source_system": "slack",
        "statement": "Bluecrest gateway experienced 3x p99 latency spikes during INC-2026.",
    },
    {
        "id": "e4",
        "source": "PR-99501",
        "target": "INC-2026",
        "type": "RESOLVES",
        "label": "RESOLVES",
        "source_system": "github",
        "statement": "PR-99501 hotfix rollback fully mitigated and resolved INC-2026.",
    },
    {
        "id": "e5",
        "source": "PR-99501",
        "target": "REL-311",
        "type": "REVERTS",
        "label": "REVERTS",
        "source_system": "github",
        "statement": "Emergency PR-99501 reverted the faulty tokenizer introduced in REL-311.",
    },
    {
        "id": "e6",
        "source": "PR-99501",
        "target": "RFC-881",
        "type": "STANDARDIZES",
        "label": "STANDARDIZES",
        "source_system": "github",
        "statement": "PR-99501 implemented the architectural guardrails defined in RFC-881 ADR.",
    },
    {
        "id": "e7",
        "source": "REL-311",
        "target": "api-search",
        "type": "DEPENDS_ON",
        "label": "DEPENDS_ON",
        "source_system": "linear",
        "statement": "REL-311 modified tokenizer dispatch contracts inside api-search gateway.",
    },
    {
        "id": "e8",
        "source": "JIRA-4029",
        "target": "Bluecrest",
        "type": "AFFECTS",
        "label": "AFFECTS",
        "source_system": "jira",
        "statement": "JIRA-4029 tracked KMS synchronization timeouts on Bluecrest dedicated gateway.",
    },
    {
        "id": "e9",
        "source": "PR-99501",
        "target": "JIRA-4029",
        "type": "RESOLVES",
        "label": "RESOLVES",
        "source_system": "github",
        "statement": "PR-99501 resolved the replication timeout tracked under JIRA-4029.",
    },
    {
        "id": "e10",
        "source": "RFC-881",
        "target": "JIRA-4029",
        "type": "STANDARDIZES",
        "label": "STANDARDIZES",
        "source_system": "confluence",
        "statement": "RFC-881 ADR defines the standard resolution policy for JIRA-4029 key isolation.",
    },
    {
        "id": "e11",
        "source": "ENG-68910",
        "target": "cgroup-manager",
        "type": "DEPENDS_ON",
        "label": "DEPENDS_ON",
        "source_system": "linear",
        "statement": "ENG-68910 recalibrated memory limits on cgroup-manager.",
    },
    {
        "id": "e12",
        "source": "ENG-30521",
        "target": "api-search",
        "type": "DEPENDS_ON",
        "label": "DEPENDS_ON",
        "source_system": "linear",
        "statement": "ENG-30521 established interop fallback limits for api-search.",
    },
]


def build_full_graph_topology() -> FullGraphResponse:
    """Build and return the complete multi-source knowledge graph topology."""
    nodes = [
        GraphCanvasNode(
            id=n["id"],
            label=n["label"],
            type=n["type"],
            source=n["source"],
            title=n["title"],
            summary=n["summary"],
            status=n["status"],
            authority_score=n["authority_score"],
            statements_count=len(n.get("statements", [])),
            statements=n.get("statements", []),
            initial_x=n.get("initial_x", 0.0),
            initial_y=n.get("initial_y", 0.0),
        )
        for n in CANONICAL_CANVAS_NODES
    ]

    edges = [
        GraphCanvasEdge(
            id=e["id"],
            source=e["source"],
            target=e["target"],
            type=e["type"],
            label=e["label"],
            source_system=e["source_system"],
            statement=e["statement"],
            document_id=e.get("document_id"),
        )
        for e in CANONICAL_CANVAS_EDGES
    ]

    node_types: dict[str, int] = {}
    for n in nodes:
        node_types[n.type] = node_types.get(n.type, 0) + 1

    rel_types: dict[str, int] = {}
    for e in edges:
        rel_types[e.type] = rel_types.get(e.type, 0) + 1

    sources_breakdown: dict[str, int] = {}
    for n in nodes:
        sources_breakdown[n.source] = sources_breakdown.get(n.source, 0) + 1

    return FullGraphResponse(
        nodes=nodes,
        edges=edges,
        total_nodes=len(nodes),
        total_edges=len(edges),
        node_types=node_types,
        relationship_types=rel_types,
        sources_breakdown=sources_breakdown,
    )
