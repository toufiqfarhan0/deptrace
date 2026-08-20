"""
Live HydraDB OpenCypher Query Generator & Inspector (Hack Hydra Track 01 / Best Use of HydraDB).

Provides inspectable, syntax-highlighted OpenCypher queries representing graph-native
traversals executed in HydraDB for Grounded Ask, Dependency Tracing, and Incident Replay.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.retrieval.models import CypherQueryInspection


def get_cypher_for_ask(question: str, entity_name: str | None = None) -> CypherQueryInspection:
    """Generate the OpenCypher query executed for Grounded Graph RAG Question Answering."""
    target = entity_name or "INC-2026"
    query = (
        f"// 1. Match primary entity vertex in HydraDB\n"
        f"MATCH (e:Entity)\n"
        f"WHERE e.name = '{target}' OR e.canonical_id = '{target}'\n"
        f"// 2. Traverse bi-temporal provenance and statement vertices\n"
        f"MATCH (e)<-[:ABOUT]-(s:Statement)-[:EXPRESSES]->(m:Message)\n"
        f"OPTIONAL MATCH (m)-[:PART_OF_DOC]->(d:Document)\n"
        f"// 3. Return verifiable evidence with stable identifiers\n"
        f"RETURN s.id AS statement_id,\n"
        f"       s.statement_type AS type,\n"
        f"       s.fact AS text,\n"
        f"       m.id AS message_id,\n"
        f"       d.id AS document_id,\n"
        f"       d.source AS source_system\n"
        f"ORDER BY s.authority_score DESC, m.timestamp ASC\n"
        f"LIMIT 10;"
    )
    return CypherQueryInspection(
        query=query,
        purpose=f"Deterministic entity binding and multi-source statement retrieval for '{target}'.",
        nodes_matched=["Entity (e)", "Statement (s)", "Message (m)", "Document (d)"],
        relationships_traversed=["[:ABOUT]", "[:EXPRESSES]", "[:PART_OF_DOC]"],
        filtering_predicates=[f"e.name = '{target}'", "ORDER BY s.authority_score DESC, m.timestamp ASC"],
        vector_rag_limitation=(
            "Naive Vector RAG matches text fragments by cosine similarity, which blends conflicting claims "
            "across Slack, Linear, and GitHub. HydraDB OpenCypher traversal binds exact entity vertices and "
            "enforces deterministic statement provenance."
        ),
    )


def get_cypher_for_trace(entity: str, max_depth: int = 2) -> CypherQueryInspection:
    """Generate the OpenCypher query executed for Multi-Hop Dependency BFS Tracing."""
    query = (
        f"// 1. Anchor search at root entity vertex in HydraDB\n"
        f"MATCH (root:Entity {{name: '{entity}'}})\n"
        f"// 2. Execute variable-length BFS path traversal up to {max_depth} hops\n"
        f"MATCH path = (root)-[*1..{max_depth}]-(connected:Entity)\n"
        f"// 3. Extract causal relationships and intermediate statements\n"
        f"UNWIND relationships(path) AS rel\n"
        f"RETURN root.name AS source,\n"
        f"       type(rel) AS edge_type,\n"
        f"       connected.name AS target,\n"
        f"       length(path) AS hop_distance\n"
        f"ORDER BY hop_distance ASC;"
    )
    return CypherQueryInspection(
        query=query,
        purpose=f"Multi-hop Breadth-First Search (depth {max_depth}) computing the blast radius for '{entity}'.",
        nodes_matched=[f"Entity (root: {entity})", "Entity (connected)"],
        relationships_traversed=["[:RESOLVES]", "[:DEPENDS_ON]", "[:AFFECTS]", "[:BLOCKED_BY]"],
        filtering_predicates=[f"root.name = '{entity}'", f"depth <= {max_depth}"],
        vector_rag_limitation=(
            "Vector databases have no concept of transitive graph closure ($A \\rightarrow B \\rightarrow C$). "
            "Finding reverse-dependency blast radiuses requires graph-native variable-length path traversal."
        ),
    )


def get_cypher_for_timeline(entity: str) -> CypherQueryInspection:
    """Generate the OpenCypher query executed for Bi-Temporal Incident Timeline Replay."""
    query = (
        f"// 1. Identify incident and connected engineering signals\n"
        f"MATCH (i:Incident {{name: '{entity}'}})\n"
        f"MATCH (i)<-[:ABOUT|AFFECTS|RESOLVES*1..2]-(m:Message)\n"
        f"MATCH (m)-[:PART_OF_DOC]->(doc:Document)\n"
        f"// 2. Reconstruct chronological event state evolution ($T_0 \\rightarrow T_n$)\n"
        f"RETURN m.id AS event_id,\n"
        f"       m.timestamp AS event_time,\n"
        f"       doc.source AS source_system,\n"
        f"       m.phase AS incident_phase,\n"
        f"       m.content AS event_body\n"
        f"ORDER BY m.timestamp ASC;"
    )
    return CypherQueryInspection(
        query=query,
        purpose=f"Reconstruct bi-temporal event stream and evolving graph subgraphs for '{entity}'.",
        nodes_matched=["Incident (i)", "Message (m)", "Document (doc)"],
        relationships_traversed=["[:ABOUT]", "[:AFFECTS]", "[:RESOLVES]", "[:PART_OF_DOC]"],
        filtering_predicates=[f"i.name = '{entity}'", "ORDER BY m.timestamp ASC"],
        vector_rag_limitation=(
            "Vector databases collapse temporal dimensions into static embeddings. HydraDB bi-temporal queries "
            "preserve event timestamps, allowing exact step-by-step incident replay."
        ),
    )
