"""
HydraDB Smoke Test for Track 1 (EnterpriseRAG-Bench).

Validates the live HydraDB graph connection, write patterns (standalone MERGE),
and multi-hop query traversals.

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


def run_query(query: str) -> dict[str, Any]:
    if not TOKEN:
        print(
            "ERROR: HYDRA_TOKEN environment variable is not set.\n"
            "Please set HYDRA_TOKEN before running the smoke test.\n"
            "Example (PowerShell): $env:HYDRA_TOKEN = (docker exec hydradb cat /data/auth-token)\n"
            "Example (Bash):       export HYDRA_TOKEN=$(docker exec hydradb cat /data/auth-token)",
            file=sys.stderr,
        )
        sys.exit(1)

    payload = {
        "cell_id": CELL_ID,
        "query": query.strip(),
    }

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Graph-Namespace": GRAPH_NAMESPACE,
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{HYDRA_URL}/v1/graphs/{GRAPH_NAME}/query",
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        print(f"\n[HTTP {response.status_code}] HydraDB query failed:")
        print(response.text, file=sys.stderr)
        response.raise_for_status()

    return response.json()


def show(title: str, result: dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    print(result)


def main() -> None:
    print("=" * 70)
    print("HydraDB Track 1 Graph Foundation Smoke Test")
    print(f"Endpoint:   {HYDRA_URL}")
    print(f"Graph:      {GRAPH_NAME} (Namespace: {GRAPH_NAMESPACE}, Cell: {CELL_ID})")
    print("=" * 70)

    # ---------------------------------------------------------------
    # MERGE 1: Sam -> Incident
    # ---------------------------------------------------------------
    merge_1 = run_query(
        """
        MERGE
        (p:Person {
            id: 20001,
            name: 'Sam'
        })
        -[:INVOLVED_IN {
            id: 60001
        }]->
        (i:Incident {
            id: 40001,
            name: 'ACME API latency incident',
            status: 'resolved'
        })
        """
    )
    show("MERGE 1 - SAM -> INCIDENT", merge_1)

    # ---------------------------------------------------------------
    # MERGE 2: Elaine -> Incident
    # ---------------------------------------------------------------
    merge_2 = run_query(
        """
        MERGE
        (p:Person {
            id: 20002,
            name: 'Elaine'
        })
        -[:INVOLVED_IN {
            id: 60002
        }]->
        (i:Incident {
            id: 40001
        })
        """
    )
    show("MERGE 2 - ELAINE -> INCIDENT", merge_2)

    # ---------------------------------------------------------------
    # MERGE 3: ACME -> Incident
    # ---------------------------------------------------------------
    merge_3 = run_query(
        """
        MERGE
        (c:Customer {
            id: 30001,
            name: 'ACME'
        })
        -[:HAS_INCIDENT {
            id: 60003
        }]->
        (i:Incident {
            id: 40001
        })
        """
    )
    show("MERGE 3 - ACME -> INCIDENT", merge_3)

    # ---------------------------------------------------------------
    # MERGE 4: Incident -> ConfigurationChange
    # ---------------------------------------------------------------
    merge_4 = run_query(
        """
        MERGE
        (i:Incident {
            id: 40001
        })
        -[:RESOLVED_BY {
            id: 60004
        }]->
        (c:ConfigurationChange {
            id: 50001,
            change_id: 'ch_20260317_01',
            description: 'Increase ACME concurrency to 200'
        })
        """
    )
    show("MERGE 4 - INCIDENT -> CHANGE", merge_4)

    # ---------------------------------------------------------------
    # QUERY 1: People involved in the incident
    # ---------------------------------------------------------------
    query_1 = run_query(
        """
        MATCH
        (p:Person)-[:INVOLVED_IN]->(i:Incident)
        WHERE i.id = 40001
        RETURN p.name AS person
        """
    )
    show("QUERY 1 - PEOPLE INVOLVED", query_1)

    people = [row[0]["value"] for row in query_1.get("rows", [])]
    assert "Sam" in people, f"Expected 'Sam' in {people}"
    assert "Elaine" in people, f"Expected 'Elaine' in {people}"
    print(f"[PASS] Verified Query 1 results: {people}")

    # ---------------------------------------------------------------
    # QUERY 2: Customer -> Incident
    # ---------------------------------------------------------------
    query_2 = run_query(
        """
        MATCH
        (c:Customer)-[:HAS_INCIDENT]->(i:Incident)
        WHERE c.id = 30001
        RETURN
            c.name AS customer,
            i.name AS incident,
            i.status AS status
        """
    )
    show("QUERY 2 - CUSTOMER INCIDENT", query_2)

    rows_2 = [
        (row[0]["value"], row[1]["value"], row[2]["value"])
        for row in query_2.get("rows", [])
    ]
    assert ("ACME", "ACME API latency incident", "resolved") in rows_2, f"Unexpected rows: {rows_2}"
    print(f"[PASS] Verified Query 2 results: {rows_2}")

    # ---------------------------------------------------------------
    # QUERY 3: Incident -> ConfigurationChange
    # ---------------------------------------------------------------
    query_3 = run_query(
        """
        MATCH
        (i:Incident)-[:RESOLVED_BY]->(c:ConfigurationChange)
        WHERE i.id = 40001
        RETURN
            i.name AS incident,
            c.change_id AS change_id,
            c.description AS description
        """
    )
    show("QUERY 3 - INCIDENT RESOLUTION", query_3)

    rows_3 = [
        (row[0]["value"], row[1]["value"], row[2]["value"])
        for row in query_3.get("rows", [])
    ]
    assert (
        "ACME API latency incident",
        "ch_20260317_01",
        "Increase ACME concurrency to 200",
    ) in rows_3, f"Unexpected rows: {rows_3}"
    print(f"[PASS] Verified Query 3 results: {rows_3}")

    print("\n" + "=" * 70)
    print("ALL HYDRADB SMOKE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()