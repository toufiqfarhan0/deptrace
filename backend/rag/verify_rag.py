"""
Live Smoke Test for Graph RAG Pipeline (Step 8).

Executes at most 2 live question-answering calls using the existing HydraDB graph:
1. "Why did the team change the model routing?"
2. "What happened with REL-311?"

Strictly bounds Gemini API calls to at most 2. Gracefully handles missing API keys
or quota limitations without retrying.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.rag_pipeline import GraphRAGPipeline, answer_question


def run_rag_smoke_test() -> dict[str, Any]:
    print("=" * 70)
    print("Step 8: Graph RAG Smoke Test (Max 2 Gemini API Calls)")
    print("=" * 70)

    test_questions = [
        "Why did the team change the model routing?",
        "What happened with REL-311?",
    ]

    pipeline = GraphRAGPipeline()
    results: list[dict[str, Any]] = []
    calls_made = 0

    for idx, question in enumerate(test_questions, start=1):
        print("\n" + "-" * 70)
        print(f"[{idx}/2] QUESTION: {question}")
        print("-" * 70)

        calls_made += 1
        resp = pipeline.answer_question(question=question, retrieval_limit=5)

        print(f"ANSWER:\n{resp.answer}\n")
        print(f"GROUNDED:           {resp.grounded}")
        print(f"CITED EVIDENCE IDS: {resp.cited_evidence_ids}")
        print(f"TOTAL EVIDENCE:     {len(resp.evidence)}")

        if resp.evidence:
            print("\nEVIDENCE RECORDS:")
            for e_idx, item in enumerate(resp.evidence, start=1):
                stmt = f" [{item.statement_type}] {item.statement[:70]}..." if item.statement else ""
                ent = f" Entity: {item.entity_name}" if item.entity_name else ""
                print(f"  [E{e_idx}] msg_id={item.message_id} doc_id={item.document_id[:25]}...{ent}{stmt}")

        results.append({
            "question": question,
            "answer": resp.answer,
            "grounded": resp.grounded,
            "cited_ids": resp.cited_evidence_ids,
            "evidence_count": len(resp.evidence),
            "error": resp.error,
        })

        if resp.error and ("429" in resp.error or "quota" in resp.error.lower() or "ResourceExhausted" in resp.error):
            print("\nWARNING: Quota limit reached on call. Stopping smoke test cleanly.")
            break

    print("\n" + "=" * 70)
    print(f"SMOKE TEST COMPLETE: {calls_made} call(s) executed")
    print("=" * 70)

    return {
        "calls_made": calls_made,
        "results": results,
    }


def main() -> None:
    run_rag_smoke_test()


if __name__ == "__main__":
    main()
