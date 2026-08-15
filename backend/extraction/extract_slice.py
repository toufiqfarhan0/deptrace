"""
Semantic Extraction Slice Runner (Step 6 Foundation).

Executes semantic extraction on a small deterministic subset of Slack messages
using the pluggable extractor interface and displays extracted entities/statements.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.extraction.base import BaseExtractor, HeuristicExtractor
from backend.extraction.schema import SemanticExtractionRecord
from backend.extraction.selector import (
    DEFAULT_PARSED_FILE,
    select_messages_by_keywords,
    select_messages_sample,
)


def run_extraction_slice(
    extractor: BaseExtractor | None = None,
    parsed_file: Path | str = DEFAULT_PARSED_FILE,
    limit_docs: int = 3,
    max_msgs_per_doc: int = 5,
    keywords: list[str] | None = None,
) -> list[SemanticExtractionRecord]:
    """
    Select a message slice and run semantic extraction across the slice.
    """
    ext = extractor or HeuristicExtractor()

    if keywords:
        messages = select_messages_by_keywords(
            keywords=keywords,
            input_file=parsed_file,
            limit=limit_docs * max_msgs_per_doc,
        )
    else:
        messages = select_messages_sample(
            input_file=parsed_file,
            limit_documents=limit_docs,
            max_messages_per_doc=max_msgs_per_doc,
        )

    print("=" * 70)
    print("DepTrace Semantic Extraction Slice (Step 6 Foundation)")
    print(f"Extractor: {getattr(ext, 'name', ext.__class__.__name__)}")
    print(f"Messages Selected: {len(messages)}")
    print("=" * 70)

    records: list[SemanticExtractionRecord] = []
    total_entities = 0
    total_statements = 0

    for msg in messages:
        rec = ext.extract_message(msg)
        rec.validate()
        records.append(rec)
        total_entities += len(rec.entities)
        total_statements += len(rec.statements)

        print(f"\n[Doc: {rec.document_id} | Msg #{rec.message_index} by {rec.author}]")
        print(f"  Text: {rec.message_text[:100]}...")
        if rec.entities:
            print(f"  Entities ({len(rec.entities)}):")
            for ent in rec.entities:
                print(f"    - [{ent.type}] {ent.name} (conf={ent.confidence})")
        if rec.statements:
            print(f"  Statements ({len(rec.statements)}):")
            for stmt in rec.statements:
                print(f"    - ({stmt.type}) {stmt.text[:80]}...")

    print("\n" + "=" * 70)
    print("Slice Extraction Summary")
    print(f"Messages Processed: {len(records)}")
    print(f"Entities Extracted: {total_entities}")
    print(f"Statements Found:   {total_statements}")
    print("=" * 70)

    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Run semantic extraction on a message slice.")
    parser.add_argument("--docs", type=int, default=3, help="Number of documents to sample")
    parser.add_argument("--msgs-per-doc", type=int, default=5, help="Max messages per document")
    parser.add_argument("--keywords", type=str, default=None, help="Comma-separated keyword filters")
    args = parser.parse_args()

    kw_list = [k.strip() for k in args.keywords.split(",")] if args.keywords else None
    run_extraction_slice(
        limit_docs=args.docs,
        max_msgs_per_doc=args.msgs_per_doc,
        keywords=kw_list,
    )


if __name__ == "__main__":
    main()
