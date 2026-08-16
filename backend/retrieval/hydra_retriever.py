"""
HydraDB Deterministic Retrieval Layer (Step 7).

Traverses the HydraDB semantic knowledge graph to find relevant structured evidence
(Entities, Statements, and Statement->Entity ABOUT relationships) for a user query.
Preserves full provenance (message_id, document_id) for every retrieved item.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.retrieval.models import EvidenceItem, RetrievalResponse
    from backend.semantic.verify_semantic_graph import query as default_query_fn
except ImportError:
    from models import EvidenceItem, RetrievalResponse  # type: ignore[no-redef]
    from verify_semantic_graph import query as default_query_fn  # type: ignore[no-redef]


def extract_rows(result: dict[str, Any]) -> list[list[Any]]:
    """Unpack HydraDB JSON rows into plain Python values."""
    if not isinstance(result, dict):
        return []
    raw_rows = result.get("rows", [])
    if not isinstance(raw_rows, list):
        return []
    return [
        [cell.get("value") if isinstance(cell, dict) else cell for cell in row]
        if isinstance(row, list)
        else []
        for row in raw_rows
    ]


class HydraRetriever:
    """
    Deterministic Graph Retriever for HydraDB.
    """

    def __init__(
        self,
        query_fn: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        self.query_fn = query_fn or default_query_fn

    def fetch_graph_snapshot(
        self,
    ) -> tuple[
        dict[int, tuple[int, str]],  # extraction_id -> (message_id, document_id)
        list[list[Any]],             # ent_rows: [ext_id, entity_id, entity_name]
        list[list[Any]],             # stmt_rows: [ext_id, stmt_id, stmt_type, text]
        list[list[Any]],             # about_rows: [stmt_id, stmt_type, text, entity_id, entity_name]
    ]:
        """
        Fetch the current semantic graph snapshot using supported simple read queries.
        """
        # 1. Message -> SemanticExtraction
        res_ext = self.query_fn(
            """
            MATCH (m:Message)-[:HAS_SEMANTIC_EXTRACTION]->(x:SemanticExtraction)
            RETURN m.id AS message_id, x.id AS extraction_id, x.document_id AS document_id
            """
        )
        ext_rows = extract_rows(res_ext)
        ext_to_source: dict[int, tuple[int, str]] = {}
        for row in ext_rows:
            if len(row) >= 3 and row[1] is not None:
                msg_id = int(row[0]) if row[0] is not None else 0
                ext_id = int(row[1])
                doc_id = str(row[2]) if row[2] is not None else ""
                ext_to_source[ext_id] = (msg_id, doc_id)

        # 2. SemanticExtraction -> Entity (MENTIONS)
        res_ent = self.query_fn(
            """
            MATCH (x:SemanticExtraction)-[:MENTIONS]->(e)
            RETURN x.id AS extraction_id, e.id AS entity_id, e.name AS entity_name
            """
        )
        ent_rows = extract_rows(res_ent)

        # 3. SemanticExtraction -> Statement (EXPRESSES)
        res_stmt = self.query_fn(
            """
            MATCH (x:SemanticExtraction)-[:EXPRESSES]->(s:Statement)
            RETURN x.id AS extraction_id, s.id AS statement_id, s.statement_type AS statement_type, s.text AS text
            """
        )
        stmt_rows = extract_rows(res_stmt)

        # 4. Statement -> Entity (ABOUT)
        res_about = self.query_fn(
            """
            MATCH (s:Statement)-[:ABOUT]->(e)
            RETURN s.id AS statement_id, s.statement_type AS statement_type, s.text AS text, e.id AS entity_id, e.name AS entity_name
            """
        )
        about_rows = extract_rows(res_about)

        return ext_to_source, ent_rows, stmt_rows, about_rows

    def retrieve(
        self,
        query: str,
        limit: int = 10,
    ) -> RetrievalResponse:
        """
        Execute deterministic keyword retrieval against the HydraDB semantic graph.
        """
        if not isinstance(query, str) or not query.strip():
            return RetrievalResponse(query=str(query or ""), results=[], result_count=0)

        norm_query = query.strip().lower()
        query_tokens = [t for t in re.split(r"\W+", norm_query) if len(t) > 2]

        try:
            ext_to_source, ent_rows, stmt_rows, about_rows = self.fetch_graph_snapshot()
        except Exception as exc:
            print(f"HydraDB query execution error during retrieval: {exc}", file=sys.stderr)
            return RetrievalResponse(query=query, results=[], result_count=0)

        stmt_to_ext: dict[int, int] = {}
        for row in stmt_rows:
            if len(row) >= 2 and row[1] is not None and row[0] is not None:
                stmt_to_ext[int(row[1])] = int(row[0])

        candidates: list[tuple[int, EvidenceItem]] = []

        # 1. Traversal over Statement -> ABOUT -> Entity relationships (Highest priority semantic link)
        for row in about_rows:
            if len(row) < 5:
                continue
            s_id = int(row[0]) if row[0] is not None else 0
            s_type = str(row[1]) if row[1] is not None else ""
            s_text = str(row[2]) if row[2] is not None else ""
            e_id = int(row[3]) if row[3] is not None else 0
            e_name = str(row[4]) if row[4] is not None else ""

            ext_id = stmt_to_ext.get(s_id)
            msg_id, doc_id = ext_to_source.get(ext_id, (0, "")) if ext_id is not None else (0, "")

            e_norm = e_name.lower()
            s_norm = s_text.lower()

            score = 0
            match_type = ""

            if norm_query == e_norm:
                score = 100
                match_type = "exact_entity"
            elif norm_query in e_norm or e_norm in norm_query:
                score = 85
                match_type = "partial_entity"
            elif norm_query in s_norm:
                score = 75
                match_type = "exact_statement"
            elif any(token in s_norm for token in query_tokens):
                score = 50
                match_type = "partial_statement"

            if score > 0:
                item = EvidenceItem(
                    message_id=msg_id,
                    document_id=doc_id,
                    entity_name=e_name,
                    statement=s_text,
                    statement_type=s_type,
                    relationship="ABOUT",
                    match_type=match_type,
                )
                candidates.append((score, item))

        # 2. SemanticExtraction -> MENTIONS -> Entity
        for row in ent_rows:
            if len(row) < 3:
                continue
            ext_id = int(row[0]) if row[0] is not None else 0
            e_id = int(row[1]) if row[1] is not None else 0
            e_name = str(row[2]) if row[2] is not None else ""
            e_norm = e_name.lower()

            msg_id, doc_id = ext_to_source.get(ext_id, (0, ""))

            score = 0
            match_type = ""

            if norm_query == e_norm:
                score = 70
                match_type = "exact_entity"
            elif norm_query in e_norm or e_norm in norm_query:
                score = 60
                match_type = "partial_entity"
            elif any(token in e_norm for token in query_tokens):
                score = 45
                match_type = "partial_entity"

            if score > 0:
                item = EvidenceItem(
                    message_id=msg_id,
                    document_id=doc_id,
                    entity_name=e_name,
                    relationship="MENTIONS",
                    match_type=match_type,
                )
                candidates.append((score, item))

        # 3. SemanticExtraction -> EXPRESSES -> Statement
        for row in stmt_rows:
            if len(row) < 4:
                continue
            ext_id = int(row[0]) if row[0] is not None else 0
            s_id = int(row[1]) if row[1] is not None else 0
            s_type = str(row[2]) if row[2] is not None else ""
            s_text = str(row[3]) if row[3] is not None else ""
            s_norm = s_text.lower()

            msg_id, doc_id = ext_to_source.get(ext_id, (0, ""))

            score = 0
            match_type = ""

            if norm_query in s_norm:
                score = 55
                match_type = "exact_statement"
            elif any(token in s_norm for token in query_tokens):
                score = 30
                match_type = "partial_statement"

            if score > 0:
                item = EvidenceItem(
                    message_id=msg_id,
                    document_id=doc_id,
                    statement=s_text,
                    statement_type=s_type,
                    relationship="EXPRESSES",
                    match_type=match_type,
                )
                candidates.append((score, item))

        # Deduplication: keep highest score for each distinct evidence tuple
        unique_items: dict[tuple[int, str | None, str | None, str | None], tuple[int, EvidenceItem]] = {}
        for score, item in candidates:
            dedup_key = (
                item.message_id,
                item.statement,
                item.entity_name,
                item.relationship,
            )
            if dedup_key not in unique_items or score > unique_items[dedup_key][0]:
                unique_items[dedup_key] = (score, item)

        # Deterministic sort: descending score, then message_id, then statement length
        sorted_candidates = sorted(
            unique_items.values(),
            key=lambda entry: (
                -entry[0],
                entry[1].message_id,
                -(len(entry[1].statement or "")),
                entry[1].entity_name or "",
            ),
        )

        final_results = [item for _, item in sorted_candidates[:limit]]

        return RetrievalResponse(
            query=query,
            results=final_results,
            result_count=len(final_results),
        )


def retrieve(
    query: str,
    limit: int = 10,
    query_fn: Callable[[str], dict[str, Any]] | None = None,
) -> RetrievalResponse:
    """Convenience function for deterministic retrieval."""
    retriever = HydraRetriever(query_fn=query_fn)
    return retriever.retrieve(query=query, limit=limit)
