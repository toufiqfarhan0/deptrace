"""
HydraDB Deterministic Dependency Tracer & Impact Analysis (Step 11).

Traverses multi-hop dependency chains, component co-occurrences, and statement
timelines over the HydraDB semantic graph with zero LLM inference.
"""

from __future__ import annotations

import os
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.retrieval.models import (
        DependencyTraceResponse,
        EvidenceItem,
        StatementTimelineItem,
        TraceHop,
        TraceImpactSummary,
    )
    from backend.semantic.verify_semantic_graph import query as default_query_fn
except ImportError:
    from models import (  # type: ignore[no-redef]
        DependencyTraceResponse,
        EvidenceItem,
        StatementTimelineItem,
        TraceHop,
        TraceImpactSummary,
    )
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


class DependencyTracer:
    """
    Deterministic Dependency Tracer for HydraDB.
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

    def get_available_entities(self) -> list[str]:
        """Return a sorted list of all unique entity names present in the graph."""
        try:
            _, ent_rows, _, about_rows = self.fetch_graph_snapshot()
        except Exception as exc:
            print(f"Error fetching entities for trace: {exc}", file=sys.stderr)
            return []

        names: set[str] = set()
        for r in ent_rows:
            if len(r) >= 3 and r[2]:
                names.add(str(r[2]).strip())
        for r in about_rows:
            if len(r) >= 5 and r[4]:
                names.add(str(r[4]).strip())

        return sorted(names)

    def trace(
        self,
        entity: str,
        max_depth: int = 2,
        limit: int = 20,
    ) -> DependencyTraceResponse:
        """
        Execute multi-hop dependency tracing starting from a target entity.
        """
        if not isinstance(entity, str) or not entity.strip():
            empty_summary = TraceImpactSummary(root_entity=str(entity or ""))
            return DependencyTraceResponse(
                root_entity=str(entity or ""),
                found=False,
                impact_summary=empty_summary,
                error="Target entity cannot be empty.",
            )

        clean_entity = entity.strip()

        try:
            ext_to_source, ent_rows, stmt_rows, about_rows = self.fetch_graph_snapshot()
        except Exception as exc:
            err_msg = f"HydraDB query error during dependency trace: {exc}"
            empty_summary = TraceImpactSummary(root_entity=clean_entity)
            return DependencyTraceResponse(
                root_entity=clean_entity,
                found=False,
                impact_summary=empty_summary,
                error=err_msg,
            )

        # -------------------------------------------------------------------
        # Build in-memory graph index from snapshot
        # -------------------------------------------------------------------
        # stmt_id -> entity_name (from ABOUT)
        stmt_to_about_entity: dict[int, str] = {}
        for r in about_rows:
            if len(r) >= 5 and r[0] is not None and r[4]:
                stmt_to_about_entity[int(r[0])] = str(r[4]).strip()

        # ext_id -> list of statements: [(stmt_id, stmt_type, text)]
        ext_to_stmts: dict[int, list[tuple[int, str, str]]] = {}
        for r in stmt_rows:
            if len(r) >= 4 and r[0] is not None and r[1] is not None:
                ext_id = int(r[0])
                stmt_id = int(r[1])
                stype = str(r[2] or "fact")
                stext = str(r[3] or "")
                ext_to_stmts.setdefault(ext_id, []).append((stmt_id, stype, stext))

        # entity_name -> set of (ext_id, message_id, doc_id)
        # ext_id -> set of entity_names
        entity_to_sources: dict[str, set[tuple[int, int, str]]] = {}
        ext_to_entities: dict[int, set[str]] = {}

        # Index from MENTIONS
        for r in ent_rows:
            if len(r) >= 3 and r[0] is not None and r[2]:
                ext_id = int(r[0])
                ent_name = str(r[2]).strip()
                msg_id, doc_id = ext_to_source.get(ext_id, (0, ""))
                entity_to_sources.setdefault(ent_name, set()).add((ext_id, msg_id, doc_id))
                ext_to_entities.setdefault(ext_id, set()).add(ent_name)

        # Index from ABOUT
        for r in about_rows:
            if len(r) >= 5 and r[0] is not None and r[4]:
                stmt_id = int(r[0])
                ent_name = str(r[4]).strip()
                for s_row in stmt_rows:
                    if len(s_row) >= 4 and int(s_row[1]) == stmt_id:
                        ext_id = int(s_row[0])
                        msg_id, doc_id = ext_to_source.get(ext_id, (0, ""))
                        entity_to_sources.setdefault(ent_name, set()).add((ext_id, msg_id, doc_id))
                        ext_to_entities.setdefault(ext_id, set()).add(ent_name)

        # -------------------------------------------------------------------
        # Resolve canonical root entity name
        # -------------------------------------------------------------------
        canonical_root = clean_entity
        if canonical_root not in entity_to_sources:
            # Case-insensitive / substring match
            lower_target = clean_entity.lower()
            matched = [name for name in entity_to_sources if lower_target == name.lower()]
            if not matched:
                matched = [name for name in entity_to_sources if lower_target in name.lower()]
            if matched:
                canonical_root = sorted(matched, key=lambda x: (len(x), x))[0]
            else:
                empty_summary = TraceImpactSummary(root_entity=clean_entity)
                return DependencyTraceResponse(
                    root_entity=clean_entity,
                    found=False,
                    impact_summary=empty_summary,
                    error=f"Entity '{clean_entity}' not found in knowledge graph.",
                )

        # -------------------------------------------------------------------
        # Multi-Hop Breadth-First Traversal
        # -------------------------------------------------------------------
        visited_entities: set[str] = {canonical_root}
        visited_in_queue: set[str] = {canonical_root}
        queue: deque[tuple[str, int]] = deque([(canonical_root, 0)])

        hops: list[TraceHop] = []
        collected_statement_tuples: list[tuple[int, str, str, str, str, str]] = []  # (msg_id, doc_id, stype, text, associated_ent, rel)
        affected_messages: set[int] = set()
        affected_documents: set[str] = set()
        actual_depth = 0

        while queue:
            curr_entity, curr_depth = queue.popleft()
            actual_depth = max(actual_depth, curr_depth)

            sources = entity_to_sources.get(curr_entity, set())
            for ext_id, msg_id, doc_id in sorted(sources):
                affected_messages.add(msg_id)
                if doc_id:
                    affected_documents.add(doc_id)

                # Collect statements from this message/extraction
                ext_stmts = ext_to_stmts.get(ext_id, [])
                for stmt_id, stype, stext in ext_stmts:
                    about_ent = stmt_to_about_entity.get(stmt_id, curr_entity)
                    rel = "ABOUT" if stmt_id in stmt_to_about_entity else "MENTIONS"
                    collected_statement_tuples.append(
                        (msg_id, doc_id, stype, stext, about_ent, rel)
                    )

                # Traverse co-occurring neighbors in the same message
                co_occurring = ext_to_entities.get(ext_id, set())
                for neighbor in sorted(co_occurring):
                    if neighbor == curr_entity:
                        continue

                    # Extract statements supporting this hop
                    hop_stmts = [
                        f"[{stype}] {stext}" for _, stype, stext in ext_stmts
                    ]

                    hop = TraceHop(
                        source_entity=curr_entity,
                        target_entity=neighbor,
                        hop_distance=curr_depth + 1,
                        via_message_id=msg_id,
                        document_id=doc_id,
                        relationship="CO_OCCURS_IN_MESSAGE",
                        statements=hop_stmts[:3],
                    )
                    hops.append(hop)

                    if curr_depth + 1 <= max_depth:
                        visited_entities.add(neighbor)
                        if curr_depth + 1 < max_depth and neighbor not in visited_in_queue:
                            visited_in_queue.add(neighbor)
                            queue.append((neighbor, curr_depth + 1))


        # -------------------------------------------------------------------
        # Deduplicate & Order Hops Deterministically
        # -------------------------------------------------------------------
        seen_hops: set[tuple[str, str, int]] = set()
        deduped_hops: list[TraceHop] = []
        for h in hops:
            key = (h.source_entity, h.target_entity, h.via_message_id)
            if key not in seen_hops:
                seen_hops.add(key)
                deduped_hops.append(h)

        deduped_hops.sort(key=lambda h: (h.hop_distance, h.source_entity, h.target_entity, h.via_message_id))
        if limit > 0:
            deduped_hops = deduped_hops[:limit]

        # -------------------------------------------------------------------
        # Build Chronological Statement Timeline
        # -------------------------------------------------------------------
        seen_stmts: set[tuple[int, str]] = set()
        ordered_timeline: list[StatementTimelineItem] = []

        # Sort statement tuples by message_id, then statement text
        sorted_stmt_tuples = sorted(
            collected_statement_tuples,
            key=lambda t: (t[0], t[3]),
        )

        for item in sorted_stmt_tuples:
            msg_id, doc_id, stype, stext, associated_ent, rel = item
            key = (msg_id, stext)
            if key not in seen_stmts:
                seen_stmts.add(key)
                timeline_item = StatementTimelineItem(
                    order_index=len(ordered_timeline) + 1,
                    message_id=msg_id,
                    document_id=doc_id,
                    statement_type=stype,
                    statement=stext,
                    associated_entity=associated_ent,
                    relationship=rel,
                )
                ordered_timeline.append(timeline_item)

        if limit > 0:
            ordered_timeline = ordered_timeline[: limit * 2]

        # -------------------------------------------------------------------
        # Build Impact Summary
        # -------------------------------------------------------------------
        stmts_by_type: dict[str, int] = {}
        for t_item in ordered_timeline:
            stmts_by_type[t_item.statement_type] = stmts_by_type.get(t_item.statement_type, 0) + 1

        linked_components = sorted([e for e in visited_entities if e != canonical_root])

        impact_summary = TraceImpactSummary(
            root_entity=canonical_root,
            traversal_depth=actual_depth,
            total_linked_entities=len(linked_components),
            total_statements=len(ordered_timeline),
            statements_by_type=stmts_by_type,
            affected_components=linked_components,
            affected_messages=sorted(affected_messages),
            affected_documents=sorted(affected_documents),
            authors=[],
            teams=[],
            channels=[],
        )

        # -------------------------------------------------------------------
        # Raw Evidence Items for downstream RAG integration
        # -------------------------------------------------------------------
        raw_evidence: list[EvidenceItem] = []
        for t_item in ordered_timeline:
            raw_evidence.append(
                EvidenceItem(
                    message_id=t_item.message_id,
                    document_id=t_item.document_id,
                    entity_name=t_item.associated_entity,
                    statement=t_item.statement,
                    statement_type=t_item.statement_type,
                    confidence=1.0,
                    relationship=t_item.relationship,
                    match_type="dependency_trace",
                )
            )

        return DependencyTraceResponse(
            root_entity=canonical_root,
            found=True,
            impact_summary=impact_summary,
            timeline=ordered_timeline,
            dependency_hops=deduped_hops,
            raw_evidence=raw_evidence,
            error=None,
        )
