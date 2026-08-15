"""
Deterministic Graph Candidate Generator for EnterpriseRAG-Bench Slack Documents.

Constructs structural graph candidates (Document, Channel, Message, Person, Team)
from parsed Slack conversation logs (slack.jsonl) with deterministic non-negative
integer IDs for HydraDB.

Node labels created:
- Document
- Channel
- Message
- Person
- Team

Relationships created:
- Document -> Channel via IN_CHANNEL
- Person -> Message via AUTHORED
- Person -> Team via MEMBER_OF
- Message -> Channel via IN_CHANNEL
- Message -> Document via PART_OF
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]

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
    / "graph-candidates"
    / "slack_graph_candidates.jsonl"
)


def stable_id(namespace: str, value: str) -> int:
    """
    Generate a deterministic non-negative 63-bit integer ID from a namespace and value.

    HydraDB OpenCypher requires non-negative integer IDs. SHA-256 is used to guarantee
    stability and idempotency across repeated runs without external state.
    """
    raw = f"{namespace}:{value}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()

    # Mask with 63 bits so the integer is always non-negative and fits in signed 64-bit int
    return int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    ) & 0x7FFFFFFFFFFFFFFF


def iter_documents(input_file: Path | str) -> Iterator[dict[str, Any]]:
    """Iterate and decode JSONL documents from input_file."""
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number} of {path}: {exc}"
                ) from exc


def build_candidate_document(document: dict[str, Any]) -> dict[str, Any]:
    """
    Transform a single parsed Slack document into deterministic graph candidate nodes
    and relationships.
    """
    document_id = document["document_id"]
    channel_name = document.get("channel") or "unknown"

    channel_id = stable_id("channel", channel_name)
    document_vertex_id = stable_id("document", document_id)

    nodes: list[dict[str, Any]] = [
        {
            "label": "Document",
            "id": document_vertex_id,
            "document_id": document_id,
            "source": document.get("source", "slack"),
        },
        {
            "label": "Channel",
            "id": channel_id,
            "name": channel_name,
        },
    ]

    relationships: list[dict[str, Any]] = [
        {
            "type": "IN_CHANNEL",
            "id": stable_id(
                "relationship",
                f"document:{document_id}:in_channel:{channel_id}",
            ),
            "from": {
                "label": "Document",
                "id": document_vertex_id,
            },
            "to": {
                "label": "Channel",
                "id": channel_id,
            },
        }
    ]

    for message_index, message in enumerate(
        document.get("messages", []),
        start=1,
    ):
        author = (message.get("author") or "unknown").strip()
        team = (message.get("team") or "unknown").strip()
        text = (message.get("text") or "").strip()

        message_id = stable_id(
            "message",
            f"{document_id}:{message_index}",
        )
        person_id = stable_id(
            "person",
            author.lower(),
        )
        team_id = stable_id(
            "team",
            team.lower(),
        )

        nodes.extend(
            [
                {
                    "label": "Message",
                    "id": message_id,
                    "document_id": document_id,
                    "message_index": message_index,
                    "author": author,
                    "team": team,
                    "channel": channel_name,
                    "text": text,
                },
                {
                    "label": "Person",
                    "id": person_id,
                    "name": author,
                },
                {
                    "label": "Team",
                    "id": team_id,
                    "name": team,
                },
            ]
        )

        # Person -> Message via AUTHORED
        relationships.append(
            {
                "type": "AUTHORED",
                "id": stable_id(
                    "relationship",
                    f"person:{person_id}:authored:message:{message_id}",
                ),
                "from": {
                    "label": "Person",
                    "id": person_id,
                },
                "to": {
                    "label": "Message",
                    "id": message_id,
                },
            }
        )

        # Person -> Team via MEMBER_OF
        relationships.append(
            {
                "type": "MEMBER_OF",
                "id": stable_id(
                    "relationship",
                    f"person:{person_id}:member_of:team:{team_id}",
                ),
                "from": {
                    "label": "Person",
                    "id": person_id,
                },
                "to": {
                    "label": "Team",
                    "id": team_id,
                },
            }
        )

        # Message -> Channel via IN_CHANNEL
        relationships.append(
            {
                "type": "IN_CHANNEL",
                "id": stable_id(
                    "relationship",
                    f"message:{message_id}:in_channel:{channel_id}",
                ),
                "from": {
                    "label": "Message",
                    "id": message_id,
                },
                "to": {
                    "label": "Channel",
                    "id": channel_id,
                },
            }
        )

        # Message -> Document via PART_OF
        relationships.append(
            {
                "type": "PART_OF",
                "id": stable_id(
                    "relationship",
                    f"message:{message_id}:part_of:document:{document_vertex_id}",
                ),
                "from": {
                    "label": "Message",
                    "id": message_id,
                },
                "to": {
                    "label": "Document",
                    "id": document_vertex_id,
                },
            }
        )

    return {
        "document_id": document_id,
        "source": "slack",
        "channel": channel_name,
        "nodes": nodes,
        "relationships": relationships,
    }


def build_all_candidates(
    input_file: Path | str = DEFAULT_INPUT_FILE,
    output_file: Path | str = DEFAULT_OUTPUT_FILE,
) -> tuple[int, int, int]:
    """
    Process all parsed Slack documents and write candidate graph records to output_file.
    Returns (document_count, total_nodes, total_relationships).
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    document_count = 0
    total_nodes = 0
    total_relationships = 0

    with output_path.open("w", encoding="utf-8") as output:
        for document in iter_documents(input_path):
            candidate = build_candidate_document(document)

            output.write(
                json.dumps(
                    candidate,
                    ensure_ascii=False,
                )
                + "\n"
            )

            document_count += 1
            total_nodes += len(candidate["nodes"])
            total_relationships += len(candidate["relationships"])

            if document_count % 500 == 0:
                print(
                    f"Processed {document_count} documents | "
                    f"nodes={total_nodes} | "
                    f"relationships={total_relationships}"
                )

    print("\nFinished building graph candidates.")
    print(f"Documents:     {document_count}")
    print(f"Nodes:         {total_nodes}")
    print(f"Relationships: {total_relationships}")
    print(f"Output:        {output_path}")

    return document_count, total_nodes, total_relationships


def main() -> None:
    build_all_candidates()


if __name__ == "__main__":
    main()