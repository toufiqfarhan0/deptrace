"""
Resumable Google Gemini Semantic Extraction Pilot Runner (Step 6G).

Supports:
- Checkpointing and loading existing extraction records from disk
- Deduplication and skipping previously extracted messages
- Appending new records immediately with flush
- Target batch limits (--limit)
- Graceful handling of Gemini rate limits and quota exhaustion
- 100% offline unit-testability via injectable extractor
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.semantic.gemini_extractor import GeminiSemanticExtractor
except ImportError:
    from gemini_extractor import GeminiSemanticExtractor  # type: ignore[no-redef]

DEFAULT_INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "sample_100.jsonl"
)

DEFAULT_OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "pilot_results.jsonl"
)

LEGACY_OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "pilot_10_results.jsonl"
)

DEFAULT_LIMIT = 10


def is_quota_or_rate_limit_error(exc: Exception) -> bool:
    """Determine whether an exception indicates quota exhaustion or rate limiting."""
    err_str = str(exc).lower()
    err_type = type(exc).__name__.lower()
    quota_indicators = [
        "429",
        "quota",
        "rate limit",
        "ratelimit",
        "resourceexhausted",
        "resource_exhausted",
        "too many requests",
        "quota exceeded",
        "quota_exceeded",
    ]
    return any(ind in err_str or ind in err_type for ind in quota_indicators)


def load_existing_results(
    output_file: Path | str = DEFAULT_OUTPUT_FILE,
    fallback_file: Path | str | None = LEGACY_OUTPUT_FILE,
) -> tuple[list[dict[str, Any]], set[int]]:
    """
    Load existing extraction records from output_file or fallback_file.
    Returns (records, completed_message_ids).
    Deduplicates records by message_id while preserving insertion order.
    """
    path = Path(output_file)
    target_path = path

    if not target_path.exists() and fallback_file:
        fallback_path = Path(fallback_file)
        if fallback_path.exists():
            target_path = fallback_path

    records: list[dict[str, Any]] = []
    completed_ids: set[int] = set()

    if not target_path.exists():
        return records, completed_ids

    with target_path.open("r", encoding="utf-8") as handle:
        for line_num, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as err:
                print(f"Warning: Skipping corrupted line {line_num} in {target_path}: {err}", file=sys.stderr)
                continue

            msg_id = record.get("message_id")
            if msg_id is None:
                continue

            msg_id_int = int(msg_id)
            if msg_id_int in completed_ids:
                continue

            completed_ids.add(msg_id_int)
            records.append(record)

    return records, completed_ids


def load_candidate_messages(
    input_file: Path | str = DEFAULT_INPUT_FILE,
    limit: int = DEFAULT_LIMIT,
) -> list[dict[str, Any]]:
    """
    Load the first `limit` candidate messages from the sample file in deterministic order.
    """
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Input sample file not found: {path}")

    messages: list[dict[str, Any]] = []
    seen_ids: set[int] = set()

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line)
            msg_id = int(msg["message_id"])
            if msg_id in seen_ids:
                continue
            seen_ids.add(msg_id)
            messages.append(msg)
            if len(messages) >= limit:
                break

    return messages


def filter_pending_messages(
    candidates: Iterable[dict[str, Any]],
    completed_ids: set[int],
) -> list[dict[str, Any]]:
    """
    Filter candidate messages to only those not yet extracted.
    """
    return [msg for msg in candidates if int(msg["message_id"]) not in completed_ids]


def run_resumable_pilot(
    input_file: Path | str = DEFAULT_INPUT_FILE,
    output_file: Path | str = DEFAULT_OUTPUT_FILE,
    limit: int = DEFAULT_LIMIT,
    resume: bool = True,
    model: str = "gemini-3.6-flash",
    extractor: Any | None = None,
) -> list[dict[str, Any]]:
    """
    Execute resumable semantic extraction up to `limit` total results.
    """
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    existing_records: list[dict[str, Any]] = []
    completed_ids: set[int] = set()

    if resume:
        fallback = LEGACY_OUTPUT_FILE if out_path.resolve() == DEFAULT_OUTPUT_FILE.resolve() else None
        existing_records, completed_ids = load_existing_results(
            output_file=out_path,
            fallback_file=fallback,
        )

        if not out_path.exists() and existing_records:
            with out_path.open("w", encoding="utf-8") as handle:
                for rec in existing_records:
                    handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
                handle.flush()


    candidates = load_candidate_messages(input_file=input_file, limit=limit)
    pending_messages = filter_pending_messages(candidates, completed_ids)

    existing_count = len(completed_ids)
    remaining_needed = max(0, limit - existing_count)
    messages_to_process = pending_messages[:remaining_needed]

    print("=" * 70)
    print("Resumable Semantic Extraction Pilot")
    print("=" * 70)
    print("Provider:         Gemini")
    print(f"Model:            {model}")
    print(f"Target limit:     {limit}")
    print(f"Existing results: {existing_count}")
    print(f"Remaining:        {len(messages_to_process)}")
    print(f"Input file:       {input_file}")
    print(f"Output file:      {out_path}")
    print("=" * 70)

    if not messages_to_process:
        print(f"\nAll {limit} target messages have already been extracted.")
        print(f"Output: {out_path}")
        return existing_records

    if extractor is None:
        extractor = GeminiSemanticExtractor(model=model)

    successful_records = list(existing_records)

    with out_path.open("a", encoding="utf-8") as handle:
        for idx, message in enumerate(messages_to_process, start=1):
            msg_id = int(message["message_id"])
            doc_id = str(message["document_id"])
            current_total = len(successful_records) + 1
            print(
                f"[{idx}/{len(messages_to_process)}] (overall {current_total}/{limit}) "
                f"Extracting msg_id={msg_id} (doc={doc_id[:35]}...)"
            )

            try:
                extraction_result = extractor.extract(message)
            except Exception as exc:
                if is_quota_or_rate_limit_error(exc):
                    print(
                        f"\n[QUOTA / RATE LIMIT] Gemini quota or rate limit reached: {exc}\n"
                        f"Stopping extraction cleanly. Preserved {len(successful_records)} successful records in {out_path}."
                    )
                    break
                else:
                    print(
                        f"\n[ERROR] Extraction failed for msg_id={msg_id}: {exc}\n"
                        f"Stopping extraction. Preserved {len(successful_records)} successful records in {out_path}."
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

            completed_ids.add(msg_id)
            successful_records.append(record)

    print()
    print("Pilot session finished.")
    print(f"Total results on disk: {len(successful_records)}")
    print(f"Output file:           {out_path}")

    return successful_records


def run_pilot() -> None:
    """Legacy entry point."""
    run_resumable_pilot()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resumable Gemini Semantic Extraction Pilot"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Target number of extracted messages (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Resume from existing output file on disk (default: True)",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT_FILE),
        help="Path to input sample messages JSONL",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_FILE),
        help="Path to output results JSONL",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.6-flash",
        help="Gemini model identifier (default: gemini-3.6-flash)",
    )

    args = parser.parse_args()

    run_resumable_pilot(
        input_file=args.input,
        output_file=args.output,
        limit=args.limit,
        resume=args.resume,
        model=args.model,
    )


if __name__ == "__main__":
    main()