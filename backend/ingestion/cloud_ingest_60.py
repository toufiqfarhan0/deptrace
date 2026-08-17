"""
HydraDB Cloud v2 60-Document Production Ingestion & Verification (Step 17C).

Ingests the complete frozen 60-document dataset (20 Slack, 20 Linear, 20 GitHub)
into HydraDB Cloud v2 with full provenance, deterministic IDs, and forceful relations.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass

from backend.ingestion.verify_multisource_ingestion import select_60_canonical_records
from backend.ingestion.canonical import CanonicalRecord

API_KEY = os.getenv("HYDRA_DB_API_KEY")
DATABASE = os.getenv("HYDRA_DATABASE", "veridex-hackhydra")
BASE_URL = os.getenv("HYDRA_BASE_URL", "https://api.hydradb.com")


def get_auth_headers() -> dict[str, str]:
    if not API_KEY:
        raise ValueError("HYDRA_DB_API_KEY environment variable is not set.")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "API-Version": "2",
    }


def record_to_cloud_item(rec: CanonicalRecord) -> dict[str, Any]:
    """Convert CanonicalRecord to HydraDB Cloud v2 app_knowledge object."""
    item: dict[str, Any] = {
        "id": rec.document_id,
        "database": DATABASE,
        "title": rec.title,
        "type": rec.source,
        "url": f"https://veridex.internal/{rec.source}/{rec.source_id}",
        "content": {
            "text": rec.content,
        },
        "tenant_metadata": {
            "source": rec.source,
        },
        "additional_metadata": {
            "veridex_source_id": rec.source_id,
            "veridex_canonical_id": str(rec.canonical_id),
            "veridex_document_id": rec.document_id,
            "author": rec.author or "unknown",
            "external_refs": rec.external_refs,
            "participants": rec.participants,
        },
    }

    if rec.channel:
        item["tenant_metadata"]["channel"] = rec.channel
    if rec.project:
        item["tenant_metadata"]["project"] = rec.project
    if rec.repository:
        item["tenant_metadata"]["repository"] = rec.repository

    if rec.external_refs:
        item["relations"] = {"ids": rec.external_refs}

    return item


def ingest_60_documents_to_cloud(batch_size: int = 15) -> dict[str, Any]:
    """
    Ingest exactly 60 canonical records into HydraDB Cloud v2.
    """
    print("=" * 80)
    print("STEP 17C: HYDRADB CLOUD V2 60-DOCUMENT PRODUCTION INGESTION")
    print(f"Target Database: {DATABASE}")
    print(f"Endpoint:        {BASE_URL}")
    print("=" * 80)

    # 1. Load and assert exact 60 canonical records
    records = select_60_canonical_records()
    total_count = len(records)
    slack_records = [r for r in records if r.source == "slack"]
    linear_records = [r for r in records if r.source == "linear"]
    github_records = [r for r in records if r.source == "github"]

    print(f"\n1. Validating Canonical Dataset...")
    print(f"   Total records:  {total_count} (Expected: 60)")
    print(f"   Slack records:  {len(slack_records)} (Expected: 20)")
    print(f"   Linear records: {len(linear_records)} (Expected: 20)")
    print(f"   GitHub records: {len(github_records)} (Expected: 20)")

    if total_count != 60 or len(slack_records) != 20 or len(linear_records) != 20 or len(github_records) != 20:
        raise ValueError(f"Dataset assertion failed: expected exactly 20 Slack, 20 Linear, 20 GitHub (60 total), got {total_count}")

    doc_ids = [r.document_id for r in records]
    unique_doc_ids = set(doc_ids)
    if len(unique_doc_ids) != 60:
        raise ValueError(f"Duplicate document IDs detected: {60 - len(unique_doc_ids)} duplicates")

    print(f"   All 60 document IDs are strictly unique.")

    # 2. Ingest records in batches
    headers = get_auth_headers()
    submitted_ids: list[str] = []
    batch_results: list[dict[str, Any]] = []

    print(f"\n2. Ingesting 60 documents in batches of {batch_size}...")
    for i in range(0, total_count, batch_size):
        batch = records[i:i + batch_size]
        app_items = [record_to_cloud_item(r) for r in batch]
        form_data = {
            "type": "knowledge",
            "database": DATABASE,
            "app_knowledge": json.dumps(app_items),
        }

        t0 = time.perf_counter()
        res = requests.post(f"{BASE_URL}/context/ingest", headers=headers, data=form_data, timeout=60)
        latency = (time.perf_counter() - t0) * 1000

        if not res.ok:
            print(f"   Batch {i // batch_size + 1} FAILED: HTTP {res.status_code} - {res.text}", file=sys.stderr)
            raise RuntimeError(f"Ingestion batch failed: {res.text}")

        res_json = res.json()
        if not res_json.get("success"):
            print(f"   Batch {i // batch_size + 1} API Error: {res_json}", file=sys.stderr)
            raise RuntimeError(f"Ingestion batch unsuccessful: {res_json}")

        data = res_json.get("data", {})
        results = data.get("results", [])
        for item_res in results:
            submitted_ids.append(item_res.get("id"))

        batch_results.append(res_json)
        print(f"   Batch {i // batch_size + 1} ({len(batch)} items) accepted: HTTP {res.status_code} ({latency:.1f}ms), relations_created={sum(r.get('relations_created', 0) for r in results)}")

    print(f"\n   Total submitted to Cloud: {len(submitted_ids)} / 60")

    # 3. Poll indexing status for all 60 documents
    print(f"\n3. Polling Indexing Status for all 60 documents...")
    pending_ids = set(submitted_ids)
    completed_ids: set[str] = set()
    poll_start = time.time()
    max_poll_seconds = 180

    while pending_ids and (time.time() - poll_start < max_poll_seconds):
        # Poll in chunks of 20 IDs
        batch_ids = list(pending_ids)[:20]
        res_status = requests.get(
            f"{BASE_URL}/context/status",
            headers=headers,
            params={"database": DATABASE, "ids": batch_ids},
            timeout=30,
        )

        if res_status.ok:
            st_json = res_status.json()
            statuses = st_json.get("data", {}).get("statuses", [])
            for st in statuses:
                doc_id = st.get("id")
                idx_status = st.get("indexing_status")
                if idx_status in ("graph_creation", "completed"):
                    completed_ids.add(doc_id)
                    pending_ids.discard(doc_id)
                elif idx_status in ("errored", "failed"):
                    raise RuntimeError(f"Document {doc_id} failed indexing: {st.get('error_message') or st.get('message')}")

        print(f"   Indexed: {len(completed_ids)} / 60 documents (Pending: {len(pending_ids)})...")
        if not pending_ids:
            break
        time.sleep(3)

    if pending_ids:
        raise TimeoutError(f"Indexing timed out after {max_poll_seconds}s. Remaining unindexed: {len(pending_ids)}")

    print(f"\n>>> 100% OF 60 DOCUMENTS SUCCESSFULLY INDEXED IN HYDRADB CLOUD! <<<")

    # 4. Post-Ingestion Representative Cloud Queries
    print(f"\n4. Executing Representative Queries Against HydraDB Cloud...")
    test_queries = [
        "What happened with REL-311?",
        "What is connected to kernel-selector?",
        "What is connected to api-search?",
        "What is PR-99501 about?",
        "What changed around request-time guard?",
    ]

    query_results: list[dict[str, Any]] = []
    headers_json = {**headers, "Content-Type": "application/json"}

    for q in test_queries:
        t0 = time.perf_counter()
        res_q = requests.post(
            f"{BASE_URL}/query",
            headers=headers_json,
            json={
                "database": DATABASE,
                "query": q,
                "type": "knowledge",
                "query_by": "hybrid",
                "mode": "thinking",
                "graph_context": True,
                "query_forceful_relations": True,
                "max_results": 5,
            },
            timeout=30,
        )
        latency_ms = (time.perf_counter() - t0) * 1000

        if not res_q.ok:
            print(f"   Query '{q}' failed: HTTP {res_q.status_code}")
            continue

        q_data = res_q.json().get("data", {})
        chunks = q_data.get("chunks", [])

        retrieved_doc_ids = [c.get("id") for c in chunks]
        retrieved_sources = [c.get("source_type") or c.get("additional_metadata", {}).get("source") for c in chunks]
        provenance_ok = all(bool(c.get("id")) and "veridex_document_id" in c.get("additional_metadata", {}) for c in chunks)

        print(f"\n   Query: \"{q}\"")
        print(f"   Latency:            {latency_ms:.1f}ms")
        print(f"   Results Count:      {len(chunks)}")
        print(f"   Retrieved Doc IDs:  {retrieved_doc_ids}")
        print(f"   Sources:            {retrieved_sources}")
        print(f"   Provenance Preserved: {provenance_ok}")
        if chunks:
            top = chunks[0]
            print(f"   Top Match:          {top.get('source_title')} (score={top.get('relevancy_score', 0):.3f})")
            print(f"   Metadata:           {top.get('additional_metadata')}")

        query_results.append({
            "query": q,
            "results_count": len(chunks),
            "doc_ids": retrieved_doc_ids,
            "sources": retrieved_sources,
            "latency_ms": latency_ms,
            "provenance_preserved": provenance_ok,
            "top_match": chunks[0] if chunks else None,
        })

    return {
        "total_count": total_count,
        "slack_count": len(slack_records),
        "linear_count": len(linear_records),
        "github_count": len(github_records),
        "indexed_count": len(completed_ids),
        "failed_count": 0,
        "duplicate_count": 0,
        "query_results": query_results,
    }


if __name__ == "__main__":
    ingest_60_documents_to_cloud()
