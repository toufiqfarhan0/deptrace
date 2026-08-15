"""
Single Message Gemini Semantic Extraction Sanity Check.
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


SAMPLE_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "sample_100.jsonl"
)


def load_first_message() -> dict:
    with SAMPLE_FILE.open("r", encoding="utf-8") as handle:
        first_line = handle.readline()
        if not first_line:
            raise RuntimeError("sample_100.jsonl is empty.")
        return json.loads(first_line)


def main() -> None:
    message = load_first_message()

    print("=" * 70)
    print("INPUT MESSAGE")
    print("=" * 70)
    print(f"message_id:  {message['message_id']}")
    print(f"document_id: {message['document_id']}")
    print(f"author:      {message.get('author')}")
    print(f"team:        {message.get('team')}")
    print(f"channel:     {message.get('channel')}")
    print()
    print(message["text"])

    extractor = GeminiSemanticExtractor()

    print()
    print("=" * 70)
    print("GEMINI EXTRACTION")
    print("=" * 70)

    result = extractor.extract(message)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()