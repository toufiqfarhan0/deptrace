from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "parsed"
    / "slack.jsonl"
)


SUSPICIOUS_AUTHORS = {
    "leah: Repro logs from customer",
    "anya: Action items",
    "jin: short summary",
}


def main() -> None:
    documents = 0
    messages = 0
    suspicious = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as handle:

        for line_number, line in enumerate(
            handle,
            start=1,
        ):
            if not line.strip():
                continue

            document = json.loads(line)

            documents += 1

            for message in document.get("messages", []):
                messages += 1

                author = message.get("author")

                if author in SUSPICIOUS_AUTHORS:
                    suspicious.append(
                        {
                            "line": line_number,
                            "document_id": document.get(
                                "document_id"
                            ),
                            "author": author,
                        }
                    )

    print(f"Documents: {documents}")
    print(f"Messages:   {messages}")
    print(f"Suspicious authors: {len(suspicious)}")

    for item in suspicious[:20]:
        print(item)


if __name__ == "__main__":
    main()