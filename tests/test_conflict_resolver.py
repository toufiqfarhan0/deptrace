"""
Unit and integration tests for Conflict Resolution Arbiter & OpenCypher Query Inspector.
"""

import pytest
from backend.api.routes import router
from backend.retrieval.conflict_resolver import (
    ENTERPRISE_CONFLICTS,
    resolve_conflicts,
)
from backend.retrieval.cypher_inspector import (
    get_cypher_for_ask,
    get_cypher_for_timeline,
    get_cypher_for_trace,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_resolve_all_conflicts():
    """Verify conflict arbiter returns all canonical enterprise contradictions."""
    res = resolve_conflicts()
    assert res.total_conflicts == len(ENTERPRISE_CONFLICTS)
    assert res.resolved_count == len(ENTERPRISE_CONFLICTS)
    assert res.error is None
    assert len(res.conflicts) > 0

    first = res.conflicts[0]
    assert first.entity == "INC-2026"
    assert first.status == "resolved"
    assert first.canonical_truth.authority_score > 0.9
    assert first.canonical_truth.source == "github"
    assert len(first.contradicting_claims) >= 1
    assert first.cypher_inspection is not None
    assert "MATCH" in first.cypher_inspection.query


def test_filter_conflicts_by_entity():
    """Verify filtering conflicts by entity name or keyword."""
    res = resolve_conflicts(entity="Bluecrest")
    assert res.total_conflicts == 1
    assert res.conflicts[0].entity == "Bluecrest"
    assert "KMS" in res.conflicts[0].topic

    res_empty = resolve_conflicts(entity="NON_EXISTENT_ENTITY_XYZ")
    assert res_empty.total_conflicts == 0


def test_cypher_inspector_ask_query():
    """Verify OpenCypher query generation for Grounded Ask."""
    insp = get_cypher_for_ask("What happened during INC-2026?", "INC-2026")
    assert "MATCH (e:Entity)" in insp.query
    assert "INC-2026" in insp.query
    assert "Statement (s)" in insp.nodes_matched
    assert "[:ABOUT]" in insp.relationships_traversed
    assert len(insp.vector_rag_limitation) > 20


def test_cypher_inspector_trace_query():
    """Verify OpenCypher query generation for BFS Trace."""
    insp = get_cypher_for_trace("PR-99501", max_depth=2)
    assert "MATCH path = (root)-[*1..2]-(connected:Entity)" in insp.query
    assert "PR-99501" in insp.query
    assert "blast radius" in insp.purpose.lower()


def test_cypher_inspector_timeline_query():
    """Verify OpenCypher query generation for Timeline Replay."""
    insp = get_cypher_for_timeline("INC-2026")
    assert "MATCH (i:Incident {name: 'INC-2026'})" in insp.query
    assert "ORDER BY m.timestamp ASC" in insp.query


def test_api_conflicts_endpoint():
    """Verify HTTP GET /api/conflicts route."""
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/api/conflicts")
    assert response.status_code == 200
    data = response.json()
    assert "conflicts" in data
    assert data["total_conflicts"] >= 4
    assert data["resolved_count"] >= 4

    response_filtered = client.get("/api/conflicts?entity=REL-311")
    assert response_filtered.status_code == 200
    data_filtered = response_filtered.json()
    assert data_filtered["total_conflicts"] == 1
    assert data_filtered["conflicts"][0]["entity"] == "REL-311"


def test_api_full_graph_endpoint():
    """Verify HTTP GET /api/graph/full route."""
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/api/graph/full")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert data["total_nodes"] >= 10
    assert data["total_edges"] >= 10
    assert "jira_ticket" in data["node_types"]
    assert "confluence_rfc" in data["node_types"]
    assert "jira" in data["sources_breakdown"]
    assert "confluence" in data["sources_breakdown"]

