"""
Message Selection Utilities for Incremental Semantic Extraction.

Provides deterministic message sampling and keyword-targeted selection
from parsed Slack documents for controlled semantic evaluation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.ingestion.build_graph_candidates import stable_id


DEFAULT_PARSED_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "parsed"
    / "slack.jsonl"
)


def iter_parsed_messages(
    input_file: Path | str = DEFAULT_PARSED_FILE,
) -> Iterator[dict[str, Any]]:
    """
    Iterate over all messages from parsed Slack documents, attaching
    full thread and document provenance to each message item.
    """
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Parsed file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            doc_id = doc.get("document_id", "unknown")
            channel = doc.get("channel", "unknown")
            source = doc.get("source", "slack")

            for idx, msg in enumerate(doc.get("messages", []), start=1):
                author = msg.get("author", "unknown")
                team = msg.get("team")
                text = msg.get("text", "")
                msg_id = stable_id("message", f"{doc_id}:{idx}")

                yield {
                    "id": msg_id,
                    "document_id": doc_id,
                    "channel": channel,
                    "source": source,
                    "message_index": idx,
                    "author": author,
                    "team": team,
                    "text": text,
                }


def select_messages_sample(
    input_file: Path | str = DEFAULT_PARSED_FILE,
    limit_documents: int = 5,
    max_messages_per_doc: int = 5,
) -> list[dict[str, Any]]:
    """
    Select a small, deterministic subset of messages from the initial documents.
    """
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Parsed file not found: {path}")

    selected: list[dict[str, Any]] = []
    doc_count = 0

    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            doc_count += 1
            doc_id = doc.get("document_id", "unknown")
            channel = doc.get("channel", "unknown")
            source = doc.get("source", "slack")

            messages = doc.get("messages", [])[:max_messages_per_doc]
            for idx, msg in enumerate(messages, start=1):
                msg_id = stable_id("message", f"{doc_id}:{idx}")
                selected.append(
                    {
                        "id": msg_id,
                        "document_id": doc_id,
                        "channel": channel,
                        "source": source,
                        "message_index": idx,
                        "author": msg.get("author", "unknown"),
                        "team": msg.get("team"),
                        "text": msg.get("text", ""),
                    }
                )

            if doc_count >= limit_documents:
                break

    return selected


def select_messages_by_keywords(
    keywords: list[str],
    input_file: Path | str = DEFAULT_PARSED_FILE,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Select up to `limit` messages matching any of the specified keywords.
    """
    lowered_keywords = [k.lower() for k in keywords]
    selected: list[dict[str, Any]] = []

    for msg in iter_parsed_messages(input_file):
        text_lower = msg["text"].lower()
        if any(kw in text_lower for kw in lowered_keywords):
            selected.append(msg)
            if len(selected) >= limit:
                break

    return selected
