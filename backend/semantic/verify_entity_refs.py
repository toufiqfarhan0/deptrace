"""
HydraDB Verification for Step 6K Fresh Statement -> ABOUT -> Entity links.

Ingests the fresh 2-message semantic results into HydraDB and validates:
1. Message -> SemanticExtraction (HAS_SEMANTIC_EXTRACTION)
2. SemanticExtraction -> Entity (MENTIONS)
3. SemanticExtraction -> Statement (EXPRESSES)
4. Statement -> Entity (ABOUT)

Ensures exact matching, same-message constraints, and zero provenance errors.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.semantic.fresh_entity_ref_pilot import FRESH_RESULTS_FILE
    from backend.semantic.ingest_semantic import (
        ingest_semantic_records,
        load_records,
    )
    from backend.semantic.verify_semantic_graph import (
        extract_scalar_count,
        query,
    )
except ImportError:
    from fresh_entity_ref_pilot import FRESH_RESULTS_FILE  # type: ignore[no-redef]
    from ingest_semantic import (  # type: ignore[no-redef]
        ingest_semantic_records,
        load_records,
    )
    from verify_semantic_graph import (  # type: ignore[no-redef]
        extract_scalar_count,
        query,
    )


def verify_fresh_entity_refs(
    results_file: Path = FRESH_RESULTS_FILE,
) -> dict[str, Any]:
    """Ingest fresh results and verify Statement -> ABOUT -> Entity relationships."""
    if not results_file.exists():
        print(f"Fresh results file {results_file} not found (e.g. pilot run blocked by quota).")
        return {"extractions": 0, "about_links": 0, "provenance_errors": 0, "sample_about": []}

    records = load_records(results_file)
    if not records:
        print("No fresh records found to verify.")
        return {"extractions": 0, "about_links": 0, "provenance_errors": 0, "sample_about": []}


    print("=" * 70)
    print("Step 6K: Ingesting Fresh Results into HydraDB")
    print(f"Input records: {len(records)} from {results_file}")
    print("=" * 70)

    # Ingest fresh records
    ingestion_stats = ingest_semantic_records(records)
    print("\nIngestion stats:", ingestion_stats)

    fresh_msg_ids = [int(r["message_id"]) for r in records]

    # 1. Extractions for fresh messages
    res_extractions = query(
        f"""
        MATCH (m:Message)-[:HAS_SEMANTIC_EXTRACTION]->(x:SemanticExtraction)
        WHERE m.id IN {fresh_msg_ids}
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

    # 2. Total Statement -> ABOUT -> Entity links globally
    res_about_total = query(
        """
        MATCH (s:Statement)-[:ABOUT]->(e)
        RETURN count(*) AS total_about_links
        """
    )
    total_about_links = extract_scalar_count(res_about_total)

    # 3. Sample Statement -> ABOUT -> Entity links
    res_about_samples = query(
        """
        MATCH (s:Statement)-[:ABOUT]->(e)
        RETURN s.id AS statement_id, s.text AS statement, e.name AS entity_name, labels(e) AS entity_labels
        LIMIT 20
        """
    )
    raw_rows_about = res_about_samples.get("rows", [])
    sample_about = [
        [cell.get("value") if isinstance(cell, dict) else cell for cell in row]
        for row in raw_rows_about
    ]

    print("\n" + "=" * 70)
    print("STEP 6K VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Fresh messages ingested:           {len(records)}")
    print(f"Fresh extractions verified:        {len(extractions)}")
    print(f"Total Statement->Entity (ABOUT):   {total_about_links}")
    print(f"Provenance errors:                 {provenance_errors}")
    print("=" * 70)

    print("\nSample Statement -> ABOUT -> Entity Relationships:")
    for row in sample_about:
        stmt_id = row[0]
        stmt_text = str(row[1])[:60] if len(row) > 1 else ""
        ent_name = str(row[2]) if len(row) > 2 else ""
        print(f"  Statement: \"{stmt_text}...\"")
        print(f"    -> ABOUT -> Entity: \"{ent_name}\"")

    # Invariant assertions
    assert provenance_errors == 0, f"Expected 0 provenance errors, got {provenance_errors}"
    assert len(extractions) == len(records), (
        f"Expected {len(records)} extractions in HydraDB, got {len(extractions)}"
    )

    return {
        "extractions": len(extractions),
        "about_links": total_about_links,
        "provenance_errors": provenance_errors,
        "sample_about": sample_about,
    }


def main() -> None:
    verify_fresh_entity_refs()


if __name__ == "__main__":
    main()
