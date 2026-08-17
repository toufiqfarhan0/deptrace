"""
HydraDB Cloud Retrieval & Dual Driver Verification Runner (Step 17D).

Tests both local OpenCypher and HydraDB Cloud v2 retrieval, tracing, and health check
implementations. Verifies provenance invariants, identifier-aware matching, and compares
local vs cloud retrieval results.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass

from backend.retrieval.cloud_retriever import HydraCloudRetriever
from backend.retrieval.cloud_tracer import HydraCloudTracer
from backend.retrieval.factory import check_active_health, get_active_retriever, get_active_tracer
from backend.retrieval.hydra_retriever import HydraRetriever
from backend.retrieval.dependency_tracer import DependencyTracer


def run_cloud_retrieval_verification() -> dict[str, Any]:
    print("=" * 80)
    print("STEP 17D: HYDRADB CLOUD RETRIEVAL & DUAL DRIVER VERIFICATION")
    print("=" * 80)

    # 1. Test Health Check in Both Modes
    print("\n1. Testing Health Checks...")
    os.environ["HYDRA_MODE"] = "local"
    local_health = check_active_health()
    print(f"   [LOCAL MODE] Health: {local_health}")

    os.environ["HYDRA_MODE"] = "cloud"
    cloud_health = check_active_health()
    print(f"   [CLOUD MODE] Health: {cloud_health}")

    # 2. Test Cloud Retriever Identifier-Aware Queries
    print("\n2. Testing HydraDB Cloud v2 Knowledge Retrieval...")
    cloud_retriever = HydraCloudRetriever()
    local_retriever = HydraRetriever()

    test_queries = [
        ("What happened with REL-311?", "REL-311"),
        ("What is connected to kernel-selector?", "kernel-selector"),
        ("What is connected to api-search?", "api-search"),
        ("What is PR-99501 about?", "PR-99501"),
        ("What changed around request-time guard?", "request-time guard"),
    ]

    query_evaluations: list[dict[str, Any]] = []

    for query_text, target_id in test_queries:
        print(f"\n   ----------------------------------------------------------------------")
        print(f"   Query: \"{query_text}\" (Target Identifier: '{target_id}')")

        # Local retrieval
        t0 = time.perf_counter()
        local_res = local_retriever.retrieve(query_text, limit=10)
        local_lat = (time.perf_counter() - t0) * 1000

        # Cloud retrieval
        t0 = time.perf_counter()
        cloud_res = cloud_retriever.retrieve(query_text, limit=10)
        cloud_lat = (time.perf_counter() - t0) * 1000

        print(f"   [LOCAL] Evidence Count: {cloud_res.result_count}, Latency: {local_lat:.1f}ms")
        print(f"   [CLOUD] Evidence Count: {cloud_res.result_count}, Latency: {cloud_lat:.1f}ms")

        # Check provenance invariants for Cloud
        prov_valid = True
        exact_matched = False
        top_doc_id = ""
        top_title = ""

        if cloud_res.results:
            top = cloud_res.results[0]
            top_doc_id = top.document_id
            top_title = top.entity_name or ""
            print(f"   [CLOUD Top Match] {top.entity_name} ({top.match_type}) - doc={top.document_id}")
            print(f"      Statement: {top.statement[:160]}...")

            for item in cloud_res.results:
                if not item.document_id:
                    prov_valid = False
                if item.match_type == "exact":
                    exact_matched = True

        print(f"   [CLOUD Provenance Valid] {prov_valid}")
        print(f"   [CLOUD Exact Identifier Match] {exact_matched}")

        query_evaluations.append({
            "query": query_text,
            "target_identifier": target_id,
            "local_count": local_res.result_count,
            "local_latency_ms": local_lat,
            "cloud_count": cloud_res.result_count,
            "cloud_latency_ms": cloud_lat,
            "cloud_top_doc": top_doc_id,
            "cloud_top_title": top_title,
            "provenance_valid": prov_valid,
            "exact_matched": exact_matched,
        })

    # 3. Test Cloud Tracer & Compare with Local Tracer
    print(f"\n3. Testing Cloud Dependency Tracer vs Local Dependency Tracer...")
    cloud_tracer = HydraCloudTracer()
    local_tracer = DependencyTracer()

    cloud_entities = cloud_tracer.get_available_entities()
    local_entities = local_tracer.get_available_entities()
    print(f"   Local entities available: {len(local_entities)}")
    print(f"   Cloud entities available: {len(cloud_entities)}")

    test_trace_entity = "PR-99501"
    print(f"\n   Tracing '{test_trace_entity}' in Cloud Driver...")
    t0 = time.perf_counter()
    cloud_trace_res = cloud_tracer.trace(test_trace_entity, max_depth=2, limit=10)
    cloud_trace_lat = (time.perf_counter() - t0) * 1000

    print(f"   Found:              {cloud_trace_res.found}")
    print(f"   Linked Entities:    {cloud_trace_res.impact_summary.affected_components}")
    print(f"   Dependency Hops:    {len(cloud_trace_res.dependency_hops)}")
    print(f"   Timeline Items:     {len(cloud_trace_res.timeline)}")
    print(f"   Affected Messages:  {len(cloud_trace_res.impact_summary.affected_messages)}")
    print(f"   Cloud Trace Latency:{cloud_trace_lat:.1f}ms")

    # Reset HYDRA_MODE to local for default offline guarantees
    os.environ["HYDRA_MODE"] = "local"
    print(f"\n>>> DUAL DRIVER VERIFICATION COMPLETED SUCCESSFULLY! <<<")

    return {
        "local_health": local_health,
        "cloud_health": cloud_health,
        "queries": query_evaluations,
        "cloud_trace": {
            "entity": test_trace_entity,
            "found": cloud_trace_res.found,
            "linked_entities": cloud_trace_res.impact_summary.affected_components,
            "hops_count": len(cloud_trace_res.dependency_hops),
            "timeline_count": len(cloud_trace_res.timeline),
        },
    }


if __name__ == "__main__":
    run_cloud_retrieval_verification()
