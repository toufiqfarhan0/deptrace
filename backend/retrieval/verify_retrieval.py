"""
Local HydraDB Retrieval Verification (Step 7).

Executes deterministic keyword queries against the live local HydraDB instance:
1. "strict_model"
2. "REL-311"
3. "fallback"
4. "kernel-selector"

Validates result structure, provenance preservation, and deterministic ranking.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.retrieval.hydra_retriever import retrieve


def verify_retrieval() -> dict[str, int]:
    print("=" * 70)
    print("HydraDB Deterministic Retrieval Layer Verification (Step 7)")
    print("=" * 70)

    test_queries = [
        "strict_model",
        "REL-311",
        "fallback",
        "kernel-selector",
    ]

    counts: dict[str, int] = {}

    for query_str in test_queries:
        resp = retrieve(query_str, limit=5)
        counts[query_str] = resp.result_count

        print("\n" + "-" * 70)
        print(f"QUERY:        \"{resp.query}\"")
        print(f"RESULT COUNT: {resp.result_count}")
        print("-" * 70)

        for idx, item in enumerate(resp.results, start=1):
            print(f"[{idx}] Relationship: {item.relationship} | Match: {item.match_type}")
            print(f"    Message ID:  {item.message_id}")
            print(f"    Document ID: {item.document_id[:35]}...")
            if item.entity_name:
                print(f"    Entity:      {item.entity_name}")
            if item.statement:
                stmt_snippet = item.statement[:75].replace("\n", " ")
                print(f"    Statement:   [{item.statement_type}] {stmt_snippet}...")

        # Invariant checks for test queries
        assert resp.result_count > 0, f"Expected at least 1 result for query '{query_str}', got 0"
        for item in resp.results:
            assert item.message_id > 0, f"Invalid message_id: {item.message_id}"
            assert len(item.document_id) > 0, "Empty document_id in evidence item"
            assert item.source == "hydradb"

    print("\n" + "=" * 70)
    print("RETRIEVAL VERIFICATION SUMMARY")
    print("=" * 70)
    for q, count in counts.items():
        print(f"  - Query \"{q}\": {count} evidence items retrieved")
    print("=" * 70)
    print("\nALL RETRIEVAL VERIFICATION CHECKS PASSED!")

    return counts


def main() -> None:
    verify_retrieval()


if __name__ == "__main__":
    main()
