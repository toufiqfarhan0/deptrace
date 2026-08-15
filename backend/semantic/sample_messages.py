"""
Deterministic Semantic Extraction Message Sampler (Step 6B).

Builds a reproducible, category-balanced 100-message evaluation sample from
the parsed Slack dataset for semantic extraction benchmarking.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "parsed"
    / "slack.jsonl"
)

DEFAULT_OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "sample_100.jsonl"
)

TARGET_SIZE = 100


def stable_score(message_id: int) -> int:
    """
    Deterministic pseudo-random score.
    The same message_id always produces the same score, ensuring reproducible sampling.
    """
    digest = hashlib.sha256(str(message_id).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def get_message_id(document_id: str, message_index: int) -> int:
    """
    Generate deterministic 63-bit integer message ID matching candidate generation.
    """
    raw = f"message:{document_id}:{message_index}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False) & 0x7FFFFFFFFFFFFFFF


def load_messages(input_file: Path | str = DEFAULT_INPUT_FILE) -> list[dict[str, Any]]:
    """Load and parse all messages with deterministic message IDs and provenance."""
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    messages: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue

            document = json.loads(line)
            document_id = document["document_id"]
            channel = document.get("channel")

            for index, message in enumerate(
                document.get("messages", []),
                start=1,
            ):
                text = (message.get("text") or "").strip()
                if not text:
                    continue

                msg_id = get_message_id(document_id, index)

                messages.append(
                    {
                        "message_id": msg_id,
                        "document_id": document_id,
                        "message_index": index,
                        "author": message.get("author"),
                        "team": message.get("team"),
                        "channel": channel,
                        "text": text,
                    }
                )

    return messages


def classify_message(message: dict[str, Any]) -> set[str]:
    """
    Lightweight deterministic classification.
    Used exclusively to select a representative cross-category evaluation sample.
    """
    text = message["text"].lower()
    categories: set[str] = set()

    author = (message.get("author") or "").lower()
    team = (message.get("team") or "").lower()

    # Customer/support signals
    if any(
        token in text
        for token in [
            "customer",
            "client",
            "tenant",
            "account",
            "support",
        ]
    ) or any(
        token in team
        for token in [
            "support",
            "customer",
            "cs",
            "customer-success",
        ]
    ):
        categories.add("customer_support")

    # Incident / technical signals
    if any(
        token in text
        for token in [
            "incident",
            "root cause",
            "latency",
            "error",
            "5xx",
            "4xx",
            "timeout",
            "degraded",
            "rollback",
            "mitigation",
            "regression",
        ]
    ):
        categories.add("incident_technical")

    # Decision / action signals
    if any(
        token in text
        for token in [
            "decision",
            "decide",
            "approved",
            "approve",
            "plan",
            "action item",
            "action items",
            "will ",
            "proposed",
            "recommend",
            "agreed",
        ]
    ):
        categories.add("decision_action")

    # Code / commands
    if "```" in text or any(
        token in text
        for token in [
            "curl ",
            "kubectl ",
            "git ",
            "python ",
            "docker ",
            "rg ",
            "grep ",
        ]
    ):
        categories.add("code")

    # Longer reasoning messages
    if len(text) >= 800:
        categories.add("long")

    # Very short messages
    if len(text) <= 120:
        categories.add("short")

    # Multi-entity/relationship rich messages
    if text.count("@") >= 1 or text.count("->") >= 1 or text.count("→") >= 1:
        categories.add("relationship_rich")

    # Bot/system messages
    if author.endswith("-bot") or "bot" in author:
        categories.add("bot")

    return categories


def choose_from_category(
    messages: list[dict[str, Any]],
    category: str,
    target: int,
    selected_ids: set[int],
) -> list[dict[str, Any]]:
    """Select up to `target` messages matching `category` sorted by stable pseudo-random score."""
    candidates = [
        message
        for message in messages
        if message["message_id"] not in selected_ids
        and category in classify_message(message)
    ]

    candidates.sort(key=lambda message: stable_score(message["message_id"]))
    return candidates[:target]


def build_sample(
    messages: list[dict[str, Any]],
    target_size: int = TARGET_SIZE,
) -> list[dict[str, Any]]:
    """
    Construct a deterministic category-balanced sample of `target_size` messages.
    """
    selected: list[dict[str, Any]] = []
    selected_ids: set[int] = set()

    category_targets = {
        "customer_support": 15,
        "incident_technical": 20,
        "decision_action": 15,
        "code": 10,
        "long": 10,
        "short": 10,
        "relationship_rich": 10,
        "bot": 5,
    }

    # Proportional scaling if target_size != 100
    scale = target_size / TARGET_SIZE if target_size != TARGET_SIZE else 1.0

    for category, target in category_targets.items():
        scaled_target = max(1, int(target * scale)) if target_size < TARGET_SIZE else target
        picked = choose_from_category(
            messages=messages,
            category=category,
            target=scaled_target,
            selected_ids=selected_ids,
        )

        for message in picked:
            selected.append(message)
            selected_ids.add(message["message_id"])

    # Fill remaining quota via deterministic global ranking
    remaining = [
        message
        for message in messages
        if message["message_id"] not in selected_ids
    ]
    remaining.sort(key=lambda message: stable_score(message["message_id"]))

    remaining_needed = max(0, target_size - len(selected))
    selected.extend(remaining[:remaining_needed])

    # Deterministic final ordering by document_id and message_index
    selected.sort(
        key=lambda message: (
            message["document_id"],
            message["message_index"],
        )
    )

    return selected[:target_size]


def write_sample(
    messages: list[dict[str, Any]],
    output_file: Path | str = DEFAULT_OUTPUT_FILE,
) -> None:
    """Write sampled messages to output JSONL file."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        for message in messages:
            handle.write(json.dumps(message, ensure_ascii=False) + "\n")


def print_summary(
    sample: list[dict[str, Any]],
    output_file: Path | str = DEFAULT_OUTPUT_FILE,
) -> None:
    """Print statistical coverage summary of the selected sample."""
    print()
    print("=" * 70)
    print("SEMANTIC SAMPLE SUMMARY (Step 6B)")
    print("=" * 70)
    print(f"Selected messages: {len(sample)}")

    categories: dict[str, int] = {}
    for message in sample:
        for category in classify_message(message):
            categories[category] = categories.get(category, 0) + 1

    print("\nCategory coverage:")
    for category in sorted(categories):
        print(f"  {category:<20}: {categories[category]}")

    documents = {message["document_id"] for message in sample}
    print(f"\nUnique source documents: {len(documents)}")
    print(f"Output file:             {output_file}")
    print("=" * 70)


def generate_sample(
    input_file: Path | str = DEFAULT_INPUT_FILE,
    output_file: Path | str = DEFAULT_OUTPUT_FILE,
    target_size: int = TARGET_SIZE,
) -> list[dict[str, Any]]:
    """Convenience runner to load, sample, write, and summarize."""
    messages = load_messages(input_file)
    sample = build_sample(messages, target_size=target_size)
    if len(sample) != target_size:
        raise RuntimeError(f"Expected {target_size} messages, got {len(sample)}")
    write_sample(sample, output_file)
    print_summary(sample, output_file)
    return sample


def main() -> None:
    print(f"Loading messages from: {DEFAULT_INPUT_FILE}")
    generate_sample()


if __name__ == "__main__":
    main()