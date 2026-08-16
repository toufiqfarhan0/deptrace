"""
HydraDB Verification for Semantic Knowledge Graph (Step 6F).

Verifies the ingested semantic graph components:
1. Message -> SemanticExtraction (HAS_SEMANTIC_EXTRACTION)
2. SemanticExtraction -> Entity (MENTIONS)
3. SemanticExtraction -> Statement (EXPRESSES)
"""

from __future__ import annotations

import os
import sys
from typing import Any
import requests


HYDRA_URL = os.getenv("HYDRA_URL", "http://127.0.0.1:8443")
TOKEN = os.getenv("HYDRA_TOKEN", "local-development-token-32-bytes")
GRAPH_NAME = os.getenv("HYDRA_GRAPH", "default")
GRAPH_NAMESPACE = os.getenv("HYDRA_NAMESPACE", "default")
CELL_ID = os.getenv("HYDRA_CELL_ID", "cell-0")


def query(cypher: str) -> dict[str, Any]:
    if not TOKEN:
        print(
            "ERROR: HYDRA_TOKEN environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    response = requests.post(
        f"{HYDRA_URL}/v1/graphs/{GRAPH_NAME}/query",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "X-Graph-Namespace": GRAPH_NAMESPACE,
            "Content-Type": "application/json",
        },
        json={
            "cell_id": CELL_ID,
            "query": cypher.strip(),
        },
        timeout=30,
    )

    if not response.ok:
        print("HYDRADB ERROR:", file=sys.stderr)
        print(f"Status: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        response.raise_for_status()

    return response.json()


def verify_semantic_graph() -> dict[str, Any]:
    print("=" * 70)
    print("HydraDB Semantic Pilot Verification (Step 6F)")
    print(f"Endpoint: {HYDRA_URL}")
    print(f"Graph:    {GRAPH_NAME} (Namespace: {GRAPH_NAMESPACE}, Cell: {CELL_ID})")
    print("=" * 70)

    # 1. Semantic extractions
    res_extractions = query(
        """
        MATCH (m:Message)-[:HAS_SEMANTIC_EXTRACTION]->(x:SemanticExtraction)
        RETURN m.id AS message_id, x.message_id AS extraction_message_id, x.document_id AS document_id
        """
    )
    raw_rows_ext = res_extractions.get("rows", [])
    extractions = [
        [cell.get("value") if isinstance(cell, dict) else cell for cell in row]
        for row in raw_rows_ext
    ]

    provenance_errors = sum(
        1 for row in extractions if row[0] != row[1]
    )

    print(f"\n1. SEMANTIC EXTRACTIONS: {len(extractions)} found (provenance errors: {provenance_errors})")
    for row in extractions:
        doc_snippet = str(row[2])[:35] if len(row) > 2 and row[2] is not None else "N/A"
        print(f"   Message {row[0]} -> SemanticExtraction (doc: {doc_snippet}...)")

    # 2. Semantic entities
    res_entities = query(
        """
        MATCH (x:SemanticExtraction)-[:MENTIONS]->(e)
        RETURN e.id AS entity_id, e.name AS name
        LIMIT 20
        """
    )
    raw_rows_ent = res_entities.get("rows", [])
    entities = [
        [cell.get("value") if isinstance(cell, dict) else cell for cell in row]
        for row in raw_rows_ent
    ]
    print(f"\n2. SEMANTIC ENTITIES: {len(entities)} mentions found")
    for row in entities:
        print(f"   Entity: {row[1]} (id: {row[0]})")

    # 3. Statements
    res_statements = query(
        """
        MATCH (x:SemanticExtraction)-[:EXPRESSES]->(s:Statement)
        RETURN s.statement_type AS type, s.text AS statement
        LIMIT 20
        """
    )
    raw_rows_stmt = res_statements.get("rows", [])
    statements = [
        [cell.get("value") if isinstance(cell, dict) else cell for cell in row]
        for row in raw_rows_stmt
    ]
    print(f"\n3. STATEMENTS: {len(statements)} found")
    for row in statements:
        stmt_snippet = str(row[1])[:60] if len(row) > 1 and row[1] is not None else ""
        print(f"   [{row[0]}] {stmt_snippet}...")

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Semantic extractions: {len(extractions)}")
    print(f"Entity mentions:     {len(entities)}")
    print(f"Statements:          {len(statements)}")
    print(f"Provenance errors:   {provenance_errors}")
    print("=" * 70)

    return {
        "extractions": len(extractions),
        "entities": len(entities),
        "statements": len(statements),
        "provenance_errors": provenance_errors,
        "extraction_rows": extractions,
        "entity_rows": entities,
        "statement_rows": statements,
    }


def main() -> None:
    stats = verify_semantic_graph()
    assert stats["extractions"] == 7, f"Expected 7 extractions, got {stats['extractions']}"
    assert stats["entities"] == 5, f"Expected 5 entity mentions, got {stats['entities']}"
    assert stats["statements"] == 17, f"Expected 17 statements, got {stats['statements']}"
    assert stats["provenance_errors"] == 0, f"Expected 0 provenance errors, got {stats['provenance_errors']}"
    print("\nALL HYDRADB SEMANTIC VERIFICATION CHECKS PASSED!")


if __name__ == "__main__":
    main()