"""
Gemini Semantic Extraction 10-Message Pilot Runner (Step 6C).

Extracts semantic knowledge from the first 10 sample messages using
the Gemini Interactions API and writes results to JSONL.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.semantic.gemini_extractor import GeminiSemanticExtractor
except ImportError:
    from gemini_extractor import GeminiSemanticExtractor  # type: ignore[no-redef]


INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "sample_100.jsonl"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "pilot_10_results.jsonl"
)

PILOT_SIZE = 10


def load_messages(limit: int = PILOT_SIZE) -> list[dict]:
    """Load up to `limit` messages from the 100-message sample file."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    messages: list[dict] = []
    with INPUT_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            messages.append(json.loads(line))
            if len(messages) >= limit:
                break

    return messages


def run_pilot(
    input_file: Path | str = INPUT_FILE,
    output_file: Path | str = OUTPUT_FILE,
    limit: int = PILOT_SIZE,
    model: str = "gemini-2.5-flash",
) -> list[dict]:
    """Execute Gemini semantic extraction on the pilot message batch."""
    messages = load_messages(limit=limit)
    if len(messages) != limit:
        raise RuntimeError(f"Expected {limit} messages, found {len(messages)}")

    extractor = GeminiSemanticExtractor(model=model)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []

    print("=" * 70)
    print("Gemini Semantic Extraction Pilot (Step 6C)")
    print(f"Model:       {model}")
    print(f"Messages:    {limit}")
    print(f"Input file:  {input_file}")
    print(f"Output file: {output_path}")
    print("=" * 70)

    with output_path.open("w", encoding="utf-8") as output:
        for index, message in enumerate(messages, start=1):
            msg_id = message["message_id"]
            doc_id = message["document_id"]
            print(f"[{index}/{limit}] Extracting msg_id={msg_id} (doc={doc_id[:35]}...)")

            result = extractor.extract(message)

            record = {
                "message_id": msg_id,
                "document_id": doc_id,
                "source_message": message,
                "extraction": result.model_dump(mode="json"),
            }

            results.append(record)
            output.write(json.dumps(record, ensure_ascii=False) + "\n")

    print()
    print("=" * 70)
    print("Pilot Finished Successfully.")
    print(f"Messages processed: {len(results)}")
    print(f"Output written to:  {output_path}")
    print("=" * 70)

    return results


def main() -> None:
    run_pilot()


if __name__ == "__main__":
    main()