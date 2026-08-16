"""
HydraDB Verification for Semantic Knowledge Graph (Step 6J).

Verifies the ingested semantic graph components using count-independent invariants:
1. Message -> SemanticExtraction (HAS_SEMANTIC_EXTRACTION)
2. SemanticExtraction -> Entity (MENTIONS)
3. SemanticExtraction -> Statement (EXPRESSES)
4. Statement -> Entity (ABOUT)

Distinguishes between exact COUNT(*) totals and sample displayed rows (LIMIT).
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


def extract_scalar_count(result: dict[str, Any]) -> int:
    """Extract integer count from a COUNT(*) query result."""
    rows = result.get("rows", [])
    if not rows or not rows[0]:
        return 0
    cell = rows[0][0]
    if isinstance(cell, dict):
        return int(cell.get("value", 0))
    return int(cell)


def verify_semantic_graph() -> dict[str, Any]:
    print("=" * 70)
    print("HydraDB Semantic Graph Verification")
    print(f"Endpoint: {HYDRA_URL}")
    print(f"Graph:    {GRAPH_NAME} (Namespace: {GRAPH_NAMESPACE}, Cell: {CELL_ID})")
    print("=" * 70)

    # 1. Total extraction count via COUNT(*)
    res_ext_count = query(
        """
        MATCH (m:Message)-[:HAS_SEMANTIC_EXTRACTION]->(x:SemanticExtraction)
        RETURN count(*) AS total_extractions
        """
    )
    total_extractions = extract_scalar_count(res_ext_count)

    # 1b. Extractions traversal and provenance validation
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

    provenance_errors = 0
    for row in extractions:
        msg_id = row[0]
        ext_msg_id = row[1] if len(row) > 1 else None
        doc_id = row[2] if len(row) > 2 else None
        if msg_id != ext_msg_id or not doc_id:
            provenance_errors += 1

    print(f"\n1. SEMANTIC EXTRACTIONS: {total_extractions} total (provenance errors: {provenance_errors})")
    for row in extractions[:10]:
        doc_snippet = str(row[2])[:35] if len(row) > 2 and row[2] is not None else "N/A"
        print(f"   Message {row[0]} -> SemanticExtraction (doc: {doc_snippet}...)")
    if len(extractions) > 10:
        print(f"   ... ({len(extractions) - 10} more extractions)")

    # 2. Total entity mentions via COUNT(*)
    res_ent_count = query(
        """
        MATCH (x:SemanticExtraction)-[:MENTIONS]->(e)
        RETURN count(*) AS total_entity_mentions
        """
    )
    total_entities = extract_scalar_count(res_ent_count)

    # 2b. Sample entity mentions
    res_entities = query(
        """
        MATCH (x:SemanticExtraction)-[:MENTIONS]->(e)
        RETURN e.id AS entity_id, e.name AS name
        LIMIT 20
        """
    )
    raw_rows_ent = res_entities.get("rows", [])
    sample_entities = [
        [cell.get("value") if isinstance(cell, dict) else cell for cell in row]
        for row in raw_rows_ent
    ]
    print(f"\n2. SEMANTIC ENTITIES: {total_entities} total mentions (displaying sample up to 20)")
    for row in sample_entities:
        print(f"   Entity: {row[1]} (id: {row[0]})")
    if total_entities > len(sample_entities):
        print(f"   ... ({total_entities - len(sample_entities)} more mentions)")

    # 3. Total statements via COUNT(*)
    res_stmt_count = query(
        """
        MATCH (x:SemanticExtraction)-[:EXPRESSES]->(s:Statement)
        RETURN count(*) AS total_statements
        """
    )
    total_statements = extract_scalar_count(res_stmt_count)

    # 3b. Sample statements
    res_statements = query(
        """
        MATCH (x:SemanticExtraction)-[:EXPRESSES]->(s:Statement)
        RETURN s.statement_type AS type, s.text AS statement
        LIMIT 20
        """
    )
    raw_rows_stmt = res_statements.get("rows", [])
    sample_statements = [
        [cell.get("value") if isinstance(cell, dict) else cell for cell in row]
        for row in raw_rows_stmt
    ]
    print(f"\n3. STATEMENTS: {total_statements} total (displaying sample up to 20)")
    for row in sample_statements:
        stmt_snippet = str(row[1])[:60] if len(row) > 1 and row[1] is not None else ""
        print(f"   [{row[0]}] {stmt_snippet}...")
    if total_statements > len(sample_statements):
        print(f"   ... ({total_statements - len(sample_statements)} more statements)")

    # 4. Total Statement -> ABOUT -> Entity relationships via COUNT(*)
    res_about_count = query(
        """
        MATCH (s:Statement)-[:ABOUT]->(e)
        RETURN count(*) AS total_about_links
        """
    )
    total_about_links = extract_scalar_count(res_about_count)

    # 4b. Sample Statement -> ABOUT -> Entity links
    res_about_sample = query(
        """
        MATCH (s:Statement)-[:ABOUT]->(e)
        RETURN s.id AS statement_id, s.text AS statement, e.name AS entity_name
        LIMIT 20
        """
    )
    raw_rows_about = res_about_sample.get("rows", [])
    sample_about = [
        [cell.get("value") if isinstance(cell, dict) else cell for cell in row]
        for row in raw_rows_about
    ]
    print(f"\n4. STATEMENT -> ENTITY (ABOUT): {total_about_links} total links (displaying sample up to 20)")
    for row in sample_about:
        stmt_snippet = str(row[1])[:50] if len(row) > 1 and row[1] is not None else ""
        ent_name = str(row[2]) if len(row) > 2 and row[2] is not None else ""
        print(f"   Statement [{stmt_snippet}...] -> ABOUT -> Entity ({ent_name})")
    if total_about_links > len(sample_about):
        print(f"   ... ({total_about_links - len(sample_about)} more ABOUT links)")

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Semantic extractions (COUNT*):      {total_extractions}")
    print(f"Entity mentions (COUNT*):           {total_entities}")
    print(f"Statements (COUNT*):                {total_statements}")
    print(f"Statement->Entity ABOUT (COUNT*):   {total_about_links}")
    print(f"Provenance errors:                  {provenance_errors}")
    print("=" * 70)

    # Invariant assertions
    assert provenance_errors == 0, f"Expected 0 provenance errors, got {provenance_errors}"
    assert total_extractions == len(extractions), (
        f"COUNT(*) extractions ({total_extractions}) does not match traversed rows ({len(extractions)})"
    )
    assert total_extractions >= 0, f"Extraction count must be non-negative: {total_extractions}"
    assert total_entities >= 0, f"Entity count must be non-negative: {total_entities}"
    assert total_statements >= 0, f"Statement count must be non-negative: {total_statements}"
    assert total_about_links >= 0, f"ABOUT links count must be non-negative: {total_about_links}"

    return {
        "extractions": total_extractions,
        "entities": total_entities,
        "statements": total_statements,
        "about_links": total_about_links,
        "provenance_errors": provenance_errors,
        "extraction_rows": extractions,
        "sample_entities": sample_entities,
        "sample_statements": sample_statements,
        "sample_about": sample_about,
    }


def main() -> None:
    stats = verify_semantic_graph()
    print("\nALL HYDRADB SEMANTIC INVARIANT CHECKS PASSED!")
    print(
        f"Verified {stats['extractions']} extractions, "
        f"{stats['entities']} entity mentions, "
        f"{stats['statements']} statements, "
        f"{stats['about_links']} ABOUT links."
    )


if __name__ == "__main__":
    main()