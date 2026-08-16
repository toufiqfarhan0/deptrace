"""
Deterministic 2-message sample selector for Step 6K entity_refs validation.

Selects 2 rich technical messages from sample_100.jsonl containing
explicit configuration changes, named entities, and statements.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SAMPLE_100_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "sample_100.jsonl"
)

FRESH_SAMPLE_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "fresh_2_sample.jsonl"
)

# Deterministically chosen candidate message IDs (indices 12 and 13 of sample_100)
TARGET_MESSAGE_IDS = [
    452542953563317559,   # kv-cache hotfix postmortem (kernel-fallback policy)
    8537794879600693670,  # geo-phased canary partial cut (redwood route, REL-311, v3.1.1-legacy-tokenizer)
]


def select_fresh_sample(
    source_file: Path = SAMPLE_100_FILE,
    output_file: Path = FRESH_SAMPLE_FILE,
    target_ids: list[int] = TARGET_MESSAGE_IDS,
) -> list[dict[str, Any]]:
    """Select deterministic 2-message sample from sample_100.jsonl."""
    if not source_file.exists():
        raise FileNotFoundError(f"Source sample file not found: {source_file}")

    selected: list[dict[str, Any]] = []
    target_id_set = set(target_ids)

    with source_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            msg_id = int(record["message_id"])
            if msg_id in target_id_set:
                selected.append(record)
                if len(selected) == len(target_ids):
                    break

    # Maintain deterministic order matching target_ids
    selected.sort(key=lambda m: target_ids.index(int(m["message_id"])))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as handle:
        for msg in selected:
            handle.write(json.dumps(msg, ensure_ascii=False) + "\n")

    return selected


def main() -> None:
    selected = select_fresh_sample()
    print(f"Selected {len(selected)} fresh messages for Step 6K validation:")
    for msg in selected:
        print(f"  - [{msg['message_id']}] ({msg.get('author')}) {msg.get('text', '')[:70]}...")
    print(f"Saved to: {FRESH_SAMPLE_FILE}")


if __name__ == "__main__":
    main()
