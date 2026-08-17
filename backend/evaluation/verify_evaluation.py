"""
HydraDB Evaluation & Ablation Verification Script (Step 12).

Validates:
1. Deterministic graph evaluation across benchmark queries
2. Provenance invariants (every evidence item, hop, and timeline statement has valid message_id and document_id)
3. Multi-hop dependency path resolution
4. Ablation comparison: Graph Retrieval vs. Naive Text Matching
5. Deterministic latency measurement
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.evaluation.evaluation_runner import EvaluationRunner


def run_evaluation_verification() -> None:
    print("=" * 75)
    print("DeTrace / Veridex — HydraDB Evaluation & Hardening Verification (Step 12)")
    print("=" * 75)

    runner = EvaluationRunner()
    print("\nExecuting deterministic evaluation suite against HydraDB...")
    report = runner.run_evaluation()

    print(f"\n1. Overall Evaluation Metrics:")
    print(f"   Total Benchmark Queries:     {report.total_queries}")
    print(f"   Successful Queries:          {report.successful_queries} / {report.total_queries}")
    print(f"   Total Evidence Retrieved:    {report.total_evidence_retrieved}")
    print(f"   Total Dependency Hops:       {report.total_hops_traversed}")
    print(f"   Avg Retrieval Latency:       {report.average_retrieval_latency_ms:.2f} ms")
    print(f"   Avg Dependency Trace Latency:{report.average_trace_latency_ms:.2f} ms")
    print(f"   HydraDB Status:              {report.hydradb_status}")

    print("\n2. Benchmark Query Results Breakdown:")
    for idx, qr in enumerate(report.query_results, start=1):
        print(f"\n   [{idx}] Query: \"{qr.query}\"")
        print(f"       Target Entity:       {qr.target_entity or 'Auto-discovered'}")
        print(f"       Evidence Count:      {qr.evidence_count} item(s)")
        print(f"       Matched Entities:    {qr.matched_entities}")
        print(f"       Statement Types:     {qr.matched_statement_types}")
        print(f"       Graph Relationships: {qr.relationships_discovered}")
        print(f"       Source Messages:     {qr.source_message_ids}")
        print(f"       Dependency Hops:     {qr.dependency_path_count}")
        print(f"       Linked Components:   {qr.linked_components}")
        print(f"       Provenance Valid:    {qr.provenance_valid}")
        print(f"       Latency:             retrieval={qr.retrieval_latency_ms}ms, trace={qr.trace_latency_ms}ms")

    print("\n3. Provenance Invariants Check:")
    prov = report.provenance_integrity
    print(f"   Total Items Checked:         {prov.total_items_checked}")
    print(f"   Valid Items:                 {prov.valid_items}")
    print(f"   Missing Message IDs:         {prov.missing_message_ids}")
    print(f"   Missing Document IDs:        {prov.missing_document_ids}")
    print(f"   All Invariants Valid:        {prov.is_valid}")
    if prov.errors:
        print(f"   Errors: {prov.errors}")

    print("\n4. Graph vs. Naive Text Matching Ablation Comparison:")
    for idx, ab in enumerate(report.ablation_comparisons, start=1):
        print(f"\n   [{idx}] \"{ab.query}\"")
        print(f"       Graph Retrieval:    {ab.graph_evidence_count} evidence items, entities={ab.graph_entities_found}, rels={ab.graph_relationships_found}")
        print(f"       Naive Text Search:  {ab.text_matches_count} keyword matches (Relationships: {ab.text_has_graph_relationships}, Typed Statements: {ab.text_has_typed_statements})")
        print(f"       Structural Advantage: {ab.structural_advantage_summary}")

    # Assertions
    assert report.total_queries >= 5
    assert report.successful_queries >= 4
    assert report.provenance_integrity.is_valid is True
    assert report.provenance_integrity.missing_message_ids == 0
    assert report.provenance_integrity.missing_document_ids == 0
    assert len(report.ablation_comparisons) == len(report.query_results)

    print("\n" + "=" * 75)
    print("ALL STEP 12 EVALUATION AND PROVENANCE INVARIANT CHECKS PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    run_evaluation_verification()
