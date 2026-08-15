"""
HydraDB Ingestion Verification for Step 5B.

Executes and asserts multi-hop graph read queries across all 4 core relationship types:
1. Person -> Message (AUTHORED)
2. Person -> Team (MEMBER_OF)
3. Message -> Channel (IN_CHANNEL)
4. Message -> Document (PART_OF)

Configuration via environment variables:
- HYDRA_TOKEN: Authentication bearer token (Required)
- HYDRA_URL: Base HTTP endpoint (Default: http://127.0.0.1:8443)
- HYDRA_GRAPH: Target graph ID (Default: default)
- HYDRA_NAMESPACE: Target namespace (Default: default)
- HYDRA_CELL_ID: Target cell ID (Default: cell-0)
"""

from __future__ import annotations

import os
import sys
from typing import Any
import requests


HYDRA_URL = os.getenv("HYDRA_URL", "http://127.0.0.1:8443")
TOKEN = os.getenv("HYDRA_TOKEN")
GRAPH_NAME = os.getenv("HYDRA_GRAPH", "default")
GRAPH_NAMESPACE = os.getenv("HYDRA_NAMESPACE", "default")
CELL_ID = os.getenv("HYDRA_CELL_ID", "cell-0")


def query(cypher: str) -> dict[str, Any]:
    """Execute Cypher query against HydraDB HTTP API."""
    if not TOKEN:
        print(
            "ERROR: HYDRA_TOKEN environment variable is not set.\n"
            "Please set HYDRA_TOKEN before running verification.\n"
            "Example (PowerShell): $env:HYDRA_TOKEN = (docker exec hydradb cat /data/auth-token)\n"
            "Example (Bash):       export HYDRA_TOKEN=$(docker exec hydradb cat /data/auth-token)",
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
        print(f"\n[HTTP {response.status_code}] HydraDB query failed:")
        print(response.text, file=sys.stderr)
        response.raise_for_status()

    return response.json()


def show_and_verify(
    title: str,
    result: dict[str, Any],
    min_rows: int = 1,
) -> list[list[Any]]:
    """Display query results and assert minimum row count."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    columns = result.get("columns", [])
    raw_rows = result.get("rows", [])

    formatted_rows = [
        [cell.get("value") if isinstance(cell, dict) else cell for cell in row]
        for row in raw_rows
    ]

    print(f"Columns: {columns}")
    print(f"Returned {len(formatted_rows)} rows:")
    for row in formatted_rows[:5]:
        print(f"  {row}")
    if len(formatted_rows) > 5:
        print(f"  ... ({len(formatted_rows) - 5} more rows)")

    assert (
        len(formatted_rows) >= min_rows
    ), f"Expected at least {min_rows} rows for {title}, got {len(formatted_rows)}"

    print(f"[PASS] {title} verified successfully ({len(formatted_rows)} rows returned).")
    return formatted_rows


def verify_all() -> dict[str, int]:
    """Execute all verification queries and return row counts."""
    print("=" * 70)
    print("HydraDB Ingestion Verification (Step 5B)")
    print(f"Endpoint: {HYDRA_URL}")
    print(f"Graph:    {GRAPH_NAME} (Namespace: {GRAPH_NAMESPACE}, Cell: {CELL_ID})")
    print("=" * 70)

    results_count: dict[str, int] = {}

    # 1. Person -> Message via AUTHORED
    res_people = query(
        """
        MATCH (p:Person)-[:AUTHORED]->(m:Message)
        RETURN p.name AS person, m.document_id AS document, m.message_index AS msg_idx
        LIMIT 10
        """
    )
    rows_people = show_and_verify("1. PERSON -> MESSAGE (AUTHORED)", res_people)
    results_count["Person -> Message"] = len(rows_people)

    # 2. Person -> Team via MEMBER_OF
    res_teams = query(
        """
        MATCH (p:Person)-[:MEMBER_OF]->(t:Team)
        RETURN p.name AS person, t.name AS team
        LIMIT 10
        """
    )
    rows_teams = show_and_verify("2. PERSON -> TEAM (MEMBER_OF)", res_teams)
    results_count["Person -> Team"] = len(rows_teams)

    # 3. Message -> Channel via IN_CHANNEL
    res_channels = query(
        """
        MATCH (m:Message)-[:IN_CHANNEL]->(c:Channel)
        RETURN c.name AS channel, m.author AS author
        LIMIT 10
        """
    )
    rows_channels = show_and_verify("3. MESSAGE -> CHANNEL (IN_CHANNEL)", res_channels)
    results_count["Message -> Channel"] = len(rows_channels)

    # 4. Message -> Document via PART_OF
    res_docs = query(
        """
        MATCH (m:Message)-[:PART_OF]->(d:Document)
        RETURN d.document_id AS document, m.message_index AS msg_idx
        LIMIT 10
        """
    )
    rows_docs = show_and_verify("4. MESSAGE -> DOCUMENT (PART_OF)", res_docs)
    results_count["Message -> Document"] = len(rows_docs)

    print("\n" + "=" * 70)
    print("ALL 4 INGESTION VERIFICATION QUERIES PASSED SUCCESSFULLY!")
    print("=" * 70)

    return results_count


def main() -> None:
    verify_all()


if __name__ == "__main__":
    main()