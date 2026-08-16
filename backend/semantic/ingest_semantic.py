"""
Ingest Gemini semantic extraction results into HydraDB (Step 6F).

IMPORTANT:
The current HydraDB Query engine only supports one-hop MERGE
relationship patterns.

Therefore every write in this module uses:

MERGE
(source:Label {...})
-[:RELATIONSHIP {id: INTEGER}]->
(target:Label {...})

We intentionally do NOT use:
- standalone MERGE nodes
- MATCH + CREATE
- MERGE + SET
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

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.semantic.ids import stable_id
except ImportError:
    from ids import stable_id  # type: ignore[no-redef]

DEFAULT_INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "pilot_results.jsonl"
)

LEGACY_INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "enterprise-rag"
    / "semantic-samples"
    / "pilot_10_results.jsonl"
)


HYDRA_URL = os.getenv(
    "HYDRA_URL",
    "http://127.0.0.1:8443",
)

TOKEN = os.getenv(
    "HYDRA_TOKEN",
    "local-development-token-32-bytes",
)

GRAPH_NAME = os.getenv(
    "HYDRA_GRAPH",
    "default",
)

GRAPH_NAMESPACE = os.getenv(
    "HYDRA_NAMESPACE",
    "default",
)

CELL_ID = os.getenv(
    "HYDRA_CELL_ID",
    "cell-0",
)

VALID_ENTITY_TYPES = {
    "Customer",
    "Project",
    "Incident",
    "Decision",
    "ConfigurationChange",
    "Entity",
}

VALID_STATEMENT_TYPES = {
    "fact",
    "decision",
    "claim",
    "action",
    "outcome",
}

SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def cypher_string(value: str) -> str:
    """Safely quote a string for generated Cypher."""
    return (
        "'"
        + value.replace("\\", "\\\\")
        .replace("'", "\\'")
        + "'"
    )


def validate_identifier(value: str) -> str:
    """
    Validate a label/type used in generated Cypher.
    """
    if not value or not SAFE_IDENTIFIER.match(value):
        raise ValueError(f"Unsafe Cypher identifier: {value}")
    return value


def run_query(query: str) -> dict[str, Any]:
    if not TOKEN:
        raise RuntimeError("HYDRA_TOKEN is not set.")

    response = requests.post(
        f"{HYDRA_URL}/v1/graphs/{GRAPH_NAME}/query",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "X-Graph-Namespace": GRAPH_NAMESPACE,
            "Content-Type": "application/json",
        },
        json={
            "cell_id": CELL_ID,
            "query": query.strip(),
        },
        timeout=30,
    )

    if not response.ok:
        print("\n" + "=" * 70, file=sys.stderr)
        print("HYDRADB ERROR", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(f"HTTP: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        print("\nQUERY:", file=sys.stderr)
        print(query, file=sys.stderr)
        response.raise_for_status()

    return response.json()


def load_records(input_file: Path | str | None = None) -> list[dict[str, Any]]:
    if input_file is None:
        if DEFAULT_INPUT_FILE.exists():
            path = DEFAULT_INPUT_FILE
        else:
            path = LEGACY_INPUT_FILE
    else:
        path = Path(input_file)

    if not path.exists():
        raise FileNotFoundError(f"Semantic pilot file not found: {path}")

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records



def build_semantic_extraction_query(
    message_id: int,
    document_id: str,
) -> tuple[int, int, str]:
    """
    Generate query to upsert:
        Message -> SemanticExtraction
    """
    extraction_id = stable_id("semantic-extraction", str(message_id))
    relationship_id = stable_id(
        "relationship",
        f"message:{message_id}:semantic-extraction:{extraction_id}",
    )

    query = f"""
    MERGE
    (m:Message {{
        id: {message_id}
    }})
    -[:HAS_SEMANTIC_EXTRACTION {{
        id: {relationship_id}
    }}]->
    (x:SemanticExtraction {{
        id: {extraction_id},
        message_id: {message_id},
        document_id: {cypher_string(document_id)}
    }})
    """.strip()

    return extraction_id, relationship_id, query


def merge_semantic_extraction(
    message_id: int,
    document_id: str,
) -> int:
    extraction_id, _, query = build_semantic_extraction_query(message_id, document_id)
    run_query(query)
    return extraction_id


def build_entity_query(
    extraction_id: int,
    entity: dict[str, Any],
) -> tuple[int, int, str]:
    """
    Generate query to upsert:
        SemanticExtraction -> SemanticEntityType
    """
    entity_type = validate_identifier(str(entity["type"]))
    if entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(f"Unsupported semantic entity type: {entity_type}")

    name = str(entity["name"]).strip()
    if not name:
        raise ValueError("Semantic entity name cannot be empty.")

    entity_id = stable_id(entity_type, name)
    relationship_id = stable_id(
        "relationship",
        f"semantic-extraction:{extraction_id}:mentions:{entity_type}:{entity_id}",
    )
    confidence = float(entity.get("confidence", 0.0))

    query = f"""
    MERGE
    (x:SemanticExtraction {{
        id: {extraction_id}
    }})
    -[:MENTIONS {{
        id: {relationship_id},
        confidence: {confidence}
    }}]->
    (e:{entity_type} {{
        id: {entity_id},
        name: {cypher_string(name)}
    }})
    """.strip()

    return entity_id, relationship_id, query


def merge_entity_from_extraction(
    extraction_id: int,
    entity: dict[str, Any],
) -> int:
    entity_id, _, query = build_entity_query(extraction_id, entity)
    run_query(query)
    return entity_id


def build_statement_query(
    extraction_id: int,
    statement: dict[str, Any],
    index: int,
) -> tuple[int, int, str]:
    """
    Generate query to upsert:
        SemanticExtraction -> Statement
    """
    statement_type = str(statement["type"])
    if statement_type not in VALID_STATEMENT_TYPES:
        raise ValueError(f"Unsupported statement type: {statement_type}")

    text = str(statement["text"]).strip()
    if not text:
        raise ValueError("Statement text cannot be empty.")

    confidence = float(statement.get("confidence", 0.0))
    statement_id = stable_id(
        "statement",
        f"{extraction_id}:{index}:{statement_type}:{text}",
    )
    relationship_id = stable_id(
        "relationship",
        f"semantic-extraction:{extraction_id}:expresses:{statement_id}",
    )

    query = f"""
    MERGE
    (x:SemanticExtraction {{
        id: {extraction_id}
    }})
    -[:EXPRESSES {{
        id: {relationship_id},
        confidence: {confidence}
    }}]->
    (s:Statement {{
        id: {statement_id},
        statement_type: {cypher_string(statement_type)},
        text: {cypher_string(text)}
    }})
    """.strip()

    return statement_id, relationship_id, query


def merge_statement_from_extraction(
    extraction_id: int,
    statement: dict[str, Any],
    index: int,
) -> int:
    statement_id, _, query = build_statement_query(extraction_id, statement, index)
    run_query(query)
    return statement_id


def ingest_semantic_records(records: list[dict[str, Any]]) -> dict[str, int]:
    extraction_count = 0
    entity_count = 0
    statement_count = 0

    for record_index, record in enumerate(records, start=1):
        message_id = int(record["message_id"])
        document_id = str(record["document_id"])
        extraction = record.get("extraction", {})

        print(f"\n[{record_index}/{len(records)}] message_id={message_id}")

        extraction_id = merge_semantic_extraction(message_id, document_id)
        extraction_count += 1

        entities = extraction.get("entities", [])
        for entity in entities:
            merge_entity_from_extraction(extraction_id, entity)
            entity_count += 1

        statements = extraction.get("statements", [])
        for index, statement in enumerate(statements, start=1):
            merge_statement_from_extraction(extraction_id, statement, index)
            statement_count += 1

        print(f"  entities={len(entities)} statements={len(statements)}")

    return {
        "extractions": extraction_count,
        "entities": entity_count,
        "statements": statement_count,
    }


def main() -> None:
    records = load_records()
    print(f"Loaded {len(records)} semantic results.")
    counts = ingest_semantic_records(records)

    print()
    print("=" * 70)
    print("SEMANTIC HYDRADB INGESTION COMPLETE")
    print("=" * 70)
    print(f"Extractions:  {counts['extractions']}")
    print(f"Entities:     {counts['entities']}")
    print(f"Statements:   {counts['statements']}")


if __name__ == "__main__":
    main()