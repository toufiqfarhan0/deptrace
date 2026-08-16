from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PILOT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "pilot_10_results.jsonl"
)


def main() -> None:
    entity_counts = Counter()
    statement_counts = Counter()

    messages = 0
    total_entities = 0
    generic_entities = 0

    with PILOT_FILE.open(
        "r",
        encoding="utf-8",
    ) as handle:

        for line in handle:
            if not line.strip():
                continue

            record = json.loads(line)
            extraction = record["extraction"]

            messages += 1

            for entity in extraction.get(
                "entities",
                [],
            ):
                entity_counts[
                    entity["type"]
                ] += 1

                total_entities += 1

                if entity["type"] == "Entity":
                    generic_entities += 1

            for statement in extraction.get(
                "statements",
                [],
            ):
                statement_counts[
                    statement["type"]
                ] += 1

    ratio = (
        generic_entities / total_entities
        if total_entities
        else 0.0
    )

    print("=" * 70)
    print("POST-REFINEMENT PILOT")
    print("=" * 70)

    print(
        f"Messages: {messages}"
    )

    print(
        f"Total entities: {total_entities}"
    )

    print(
        f"Generic Entity: {generic_entities}"
    )

    print(
        f"Generic Entity ratio: {ratio:.1%}"
    )

    print("\nEntity distribution:")

    for name, count in entity_counts.most_common():
        print(
            f"  {name}: {count}"
        )

    print("\nStatement distribution:")

    for name, count in statement_counts.most_common():
        print(
            f"  {name}: {count}"
        )


if __name__ == "__main__":
    main()