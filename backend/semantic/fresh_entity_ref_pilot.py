"""
Step 6K Fresh 2-Message Gemini Semantic Extraction Pilot.

CRITICAL: Strictly bounded to AT MOST 2 live Gemini API calls.
Extracts semantic entities and statements containing explicit entity_refs.
Writes each result immediately and stops cleanly on quota / rate limit errors.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.semantic.fresh_entity_ref_sample import (
        FRESH_SAMPLE_FILE,
        select_fresh_sample,
    )
    from backend.semantic.gemini_extractor import GeminiSemanticExtractor
    from backend.semantic.pilot import is_quota_or_rate_limit_error
    from backend.semantic.schema import SemanticExtraction
except ImportError:
    from fresh_entity_ref_sample import (  # type: ignore[no-redef]
        FRESH_SAMPLE_FILE,
        select_fresh_sample,
    )
    from gemini_extractor import GeminiSemanticExtractor  # type: ignore[no-redef]
    from pilot import is_quota_or_rate_limit_error  # type: ignore[no-redef]
    from schema import SemanticExtraction  # type: ignore[no-redef]

FRESH_RESULTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "fresh_2_results.jsonl"
)

MAX_CALLS = 2


def run_fresh_pilot(
    input_file: Path | str = FRESH_SAMPLE_FILE,
    output_file: Path | str = FRESH_RESULTS_FILE,
    max_calls: int = MAX_CALLS,
    extractor: Any | None = None,
) -> list[dict[str, Any]]:
    """
    Run fresh semantic extraction for up to max_calls (strictly <= 2).
    """
    in_path = Path(input_file)
    out_path = Path(output_file)

    if not in_path.exists():
        print(f"Sample file {in_path} not found; generating deterministic fresh sample...")
        select_fresh_sample(output_file=in_path)

    messages: list[dict[str, Any]] = []
    with in_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                messages.append(json.loads(line))

    # Strict limit
    target_messages = messages[:max_calls]

    if extractor is None:
        try:
            extractor = GeminiSemanticExtractor()
        except Exception as exc:
            print(f"Unable to initialize Gemini extractor (e.g. missing API key or client config): {exc}")
            return []


    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Step 6K Fresh 2-Message Gemini Semantic Extraction Pilot")
    print(f"Target messages: {len(target_messages)} (Max calls limit: {max_calls})")
    print(f"Output file:     {out_path}")
    print("=" * 70)

    successful_records: list[dict[str, Any]] = []
    calls_made = 0

    with out_path.open("w", encoding="utf-8") as handle:
        for index, message in enumerate(target_messages, start=1):
            if calls_made >= max_calls:
                print(f"\nReached max API call limit ({max_calls}). Stopping.")
                break

            msg_id = int(message["message_id"])
            doc_id = str(message["document_id"])
            author = message.get("author", "unknown")

            print(f"\n[{index}/{len(target_messages)}] Extracting msg_id={msg_id} (author={author})...")
            calls_made += 1

            try:
                extraction_result = extractor.extract(message)
            except Exception as exc:
                if is_quota_or_rate_limit_error(exc):
                    print(
                        f"\n[QUOTA / RATE LIMIT] Gemini quota reached on request {calls_made}: {exc}\n"
                        f"Stopping cleanly. Preserved {len(successful_records)} successful records."
                    )
                    break
                else:
                    print(
                        f"\n[ERROR] Extraction failed for msg_id={msg_id}: {exc}\n"
                        f"Stopping cleanly. Preserved {len(successful_records)} successful records."
                    )
                    break

            record = {
                "message_id": msg_id,
                "document_id": doc_id,
                "source_message": message,
                "extraction": extraction_result.model_dump(mode="json"),
            }

            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
            successful_records.append(record)

            # Print extraction summary for this message
            entities = record["extraction"].get("entities", [])
            statements = record["extraction"].get("statements", [])
            print(f"  Success: {len(entities)} entities, {len(statements)} statements")
            for ent in entities:
                print(f"    - Entity: [{ent['type']}] {ent['name']}")
            for stmt in statements:
                refs_str = f" (refs: {stmt.get('entity_refs', [])})" if stmt.get("entity_refs") else ""
                print(f"    - Statement: [{stmt['type']}] {stmt['text'][:60]}...{refs_str}")

            if index < len(target_messages):
                time.sleep(1.0)

    print("\n" + "=" * 70)
    print(f"Fresh pilot finished: {len(successful_records)} successful extractions, {calls_made} Gemini calls made.")
    print("=" * 70)

    return successful_records


def main() -> None:
    run_fresh_pilot()


if __name__ == "__main__":
    main()
