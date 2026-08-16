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


def load_messages() -> list[dict]:
    messages: list[dict] = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line in handle:
            if not line.strip():
                continue

            messages.append(
                json.loads(line)
            )

            if len(messages) >= PILOT_SIZE:
                break

    return messages


def run_pilot() -> None:
    messages = load_messages()

    if len(messages) != PILOT_SIZE:
        raise RuntimeError(
            f"Expected {PILOT_SIZE} messages, "
            f"found {len(messages)}"
        )

    extractor = GeminiSemanticExtractor()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("Semantic Extraction Pilot")
    print("=" * 70)
    print("Provider:    Gemini")
    print(f"Model:       {extractor.model}")
    print(f"Messages:    {PILOT_SIZE}")
    print(f"Input file:  {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print("=" * 70)

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as output:

        for index, message in enumerate(
            messages,
            start=1,
        ):
            print(
                f"[{index}/{PILOT_SIZE}] "
                f"Extracting msg_id={message['message_id']} "
                f"(doc={message['document_id'][:40]}...)"
            )

            result = extractor.extract(
                message
            )

            record = {
                "message_id": message[
                    "message_id"
                ],
                "document_id": message[
                    "document_id"
                ],
                "source_message": message,
                "extraction": result.model_dump(
                    mode="json"
                ),
            }

            output.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print()
    print("Pilot complete.")
    print(f"Messages: {PILOT_SIZE}")
    print(f"Output:   {OUTPUT_FILE}")


def main() -> None:
    run_pilot()


if __name__ == "__main__":
    main()