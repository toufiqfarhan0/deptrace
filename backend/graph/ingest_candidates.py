"""
Deterministic Slack Graph Candidates Ingestion for HydraDB.

Ingests structural graph candidate documents into HydraDB using supported
OpenCypher standalone single-hop MERGE statements with embedded endpoint properties
and non-negative integer IDs.

Write Pattern:
MERGE
(source:Label {id: INTEGER, prop: 'val', ...})
-[:RELATIONSHIP {id: INTEGER}]->
(target:Label {id: INTEGER, prop: 'val', ...})

Configuration via environment variables:
- HYDRA_TOKEN: Authentication bearer token (Required)
- HYDRA_URL: Base HTTP endpoint (Default: http://127.0.0.1:8443)
- HYDRA_GRAPH: Target graph ID (Default: default)
- HYDRA_NAMESPACE: Target namespace (Default: default)
- HYDRA_CELL_ID: Target cell ID (Default: cell-0)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "graph-candidates"
    / "slack_graph_candidates.jsonl"
)

DEFAULT_DOC_LIMIT = 10

HYDRA_URL = os.getenv("HYDRA_URL", "http://127.0.0.1:8443")
TOKEN = os.getenv("HYDRA_TOKEN")
GRAPH_NAME = os.getenv("HYDRA_GRAPH", "default")
GRAPH_NAMESPACE = os.getenv("HYDRA_NAMESPACE", "default")
CELL_ID = os.getenv("HYDRA_CELL_ID", "cell-0")

SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Safe properties to embed into Cypher node endpoints for traversal
SAFE_PROPERTIES = {
    "Document": {"document_id", "source"},
    "Channel": {"name"},
    "Message": {
        "document_id",
        "message_index",
        "author",
        "team",
        "channel",
    },
    "Person": {"name"},
    "Team": {"name"},
}


def run_query(query: str) -> dict[str, Any]:
    """Execute OpenCypher query against HydraDB HTTP query endpoint."""
    if not TOKEN:
        print(
            "ERROR: HYDRA_TOKEN environment variable is not set.\n"
            "Please set HYDRA_TOKEN before running ingestion.\n"
            "Example (PowerShell): $env:HYDRA_TOKEN = (docker exec hydradb cat /data/auth-token)\n"
            "Example (Bash):       export HYDRA_TOKEN=$(docker exec hydradb cat /data/auth-token)",
            file=sys.stderr,
        )
        sys.exit(1)

    payload = {
        "cell_id": CELL_ID,
        "query": query.strip(),
    }

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Graph-Namespace": GRAPH_NAMESPACE,
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{HYDRA_URL}/v1/graphs/{GRAPH_NAME}/query",
        headers=headers,
        json=payload,
        timeout=30,
    )

    if not response.ok:
        print(f"\n[HTTP {response.status_code}] HydraDB query failed:")
        print(response.text, file=sys.stderr)
        response.raise_for_status()

    return response.json()


def validate_identifier(value: str) -> str:
    """Validate Cypher identifier against injection."""
    if not SAFE_IDENTIFIER.match(value):
        raise ValueError(f"Unsafe Cypher identifier: '{value}'")
    return value


def escape_string_property(value: str) -> str:
    """Sanitize and escape string values for Cypher property literals."""
    return (
        value.replace("\\", "")
        .replace("'", "")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def node_fragment(
    label: str,
    node_id: int,
    properties: dict[str, Any] | None = None,
) -> str:
    """Format a Cypher node fragment with integer ID and properties."""
    valid_label = validate_identifier(label)
    props = [f"id: {int(node_id)}"]

    if properties:
        for key, value in properties.items():
            valid_key = validate_identifier(key)

            if isinstance(value, str):
                escaped = escape_string_property(value)
                props.append(f"{valid_key}: '{escaped}'")
            elif isinstance(value, bool):
                props.append(f"{valid_key}: {'true' if value else 'false'}")
            elif isinstance(value, int):
                props.append(f"{valid_key}: {value}")
            elif value is None:
                continue
            else:
                raise ValueError(
                    f"Unsupported property type for {valid_key}: {type(value).__name__}"
                )

    alias = valid_label.lower()
    return f"({alias}:{valid_label} {{{', '.join(props)}}})"


def build_merge_query(relationship: dict[str, Any]) -> str:
    """
    Construct a standalone single-hop MERGE query from an enriched relationship.
    """
    source = relationship["from"]
    target = relationship["to"]

    source_label = validate_identifier(source["label"])
    target_label = validate_identifier(target["label"])
    relationship_type = validate_identifier(relationship["type"])

    source_id = int(source["id"])
    target_id = int(target["id"])
    relationship_id = int(relationship["id"])

    source_props = source.get("properties", {})
    target_props = target.get("properties", {})

    source_str = node_fragment(source_label, source_id, source_props)
    target_str = node_fragment(target_label, target_id, target_props)

    return (
        f"MERGE {source_str}"
        f"-[:{relationship_type} {{id: {relationship_id}}}]->"
        f"{target_str}"
    )


def enrich_relationship(
    candidate: dict[str, Any],
    relationship: dict[str, Any],
) -> dict[str, Any]:
    """
    Attach safe, deterministic metadata properties to relationship endpoints.
    """
    nodes = {
        (node["label"], int(node["id"])): node
        for node in candidate.get("nodes", [])
    }

    source_key = (
        relationship["from"]["label"],
        int(relationship["from"]["id"]),
    )
    target_key = (
        relationship["to"]["label"],
        int(relationship["to"]["id"]),
    )

    if source_key not in nodes:
        raise ValueError(f"Source node not found in candidate: {source_key}")
    if target_key not in nodes:
        raise ValueError(f"Target node not found in candidate: {target_key}")

    source_node = nodes[source_key]
    target_node = nodes[target_key]

    def extract_properties(node: dict[str, Any]) -> dict[str, Any]:
        label = node["label"]
        allowed = SAFE_PROPERTIES.get(label, set())
        return {k: v for k, v in node.items() if k in allowed}

    return {
        **relationship,
        "from": {
            "label": relationship["from"]["label"],
            "id": int(relationship["from"]["id"]),
            "properties": extract_properties(source_node),
        },
        "to": {
            "label": relationship["to"]["label"],
            "id": int(relationship["to"]["id"]),
            "properties": extract_properties(target_node),
        },
    }


def load_documents(
    input_file: Path | str = DEFAULT_INPUT_FILE,
    limit: int = DEFAULT_DOC_LIMIT,
) -> list[dict[str, Any]]:
    """Load up to `limit` candidate documents from input JSONL file."""
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Candidate file not found: {path}")

    documents: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            documents.append(json.loads(line))
            if limit and len(documents) >= limit:
                break

    return documents


def ingest_candidates(
    input_file: Path | str = DEFAULT_INPUT_FILE,
    limit: int = DEFAULT_DOC_LIMIT,
) -> tuple[int, int]:
    """
    Ingest up to `limit` candidate documents into HydraDB.
    Returns (documents_processed, relationships_written).
    """
    documents = load_documents(input_file=input_file, limit=limit)
    if not documents:
        raise ValueError("No candidate documents to ingest.")

    print("=" * 70)
    print("HydraDB Deterministic Candidate Ingestion (Step 5B)")
    print(f"Target:      {HYDRA_URL} (Graph: {GRAPH_NAME}, Cell: {CELL_ID})")
    print(f"Documents:   {len(documents)} (Limit: {limit})")
    print("=" * 70)

    document_count = 0
    relationship_count = 0

    for document in documents:
        document_count += 1
        doc_id = document.get("document_id", "unknown")
        relationships = document.get("relationships", [])

        print(f"\nDocument {document_count}/{len(documents)}: {doc_id}")

        for rel in relationships:
            enriched = enrich_relationship(document, rel)
            query = build_merge_query(enriched)
            run_query(query)
            relationship_count += 1

        print(f"  Written {len(relationships)} relationships.")

    print("\n" + "=" * 70)
    print("Ingestion Finished Successfully.")
    print(f"Documents processed:   {document_count}")
    print(f"Relationships written: {relationship_count}")
    print("=" * 70)

    return document_count, relationship_count


def main() -> None:
    ingest_candidates(limit=DEFAULT_DOC_LIMIT)


if __name__ == "__main__":
    main()