"""
HydraDB Enterprise Knowledge Graph Writer (Step 13B).

Formats CanonicalRecord instances into HydraDB-compatible standalone MERGE
relationship patterns with deterministic integer IDs and strict provenance.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Sequence

from backend.ingestion.canonical import CanonicalRecord
from backend.semantic.ids import stable_id
from backend.semantic.verify_semantic_graph import query as default_query_fn


def escape_cypher(val: str | None) -> str:
    """Escape quotes and backslashes for OpenCypher literals."""
    if val is None:
        return ""
    return val.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").strip()


class HydraEnterpriseWriter:
    """
    Deterministic writer that generates and executes standalone MERGE statements
    for canonical multi-source records in HydraDB.
    """

    def __init__(
        self,
        query_fn: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        self.query_fn = query_fn or default_query_fn

    def generate_merge_statements(self, record: CanonicalRecord) -> list[str]:
        """
        Generate standalone MERGE relationship queries for a CanonicalRecord.
        Strictly adheres to HydraDB query engine's single-hop MERGE pattern:
        MERGE (a:LabelA {id: INTEGER, ...})-[:REL {id: INTEGER}]->(b:LabelB {id: INTEGER, ...})
        """
        statements: list[str] = []
        doc_id_int = record.canonical_id
        safe_title = escape_cypher(record.title[:120])
        safe_source = escape_cypher(record.source)
        safe_source_id = escape_cypher(record.source_id)
        safe_doc_id = escape_cypher(record.document_id)

        # 1. Source-Specific Structural Relationship
        if record.source == "slack":
            ch_name = record.channel or "general"
            safe_ch = escape_cypher(ch_name)
            ch_id_int = stable_id("channel", safe_ch)
            edge_id = stable_id("edge_in_channel", f"{record.document_id}->{ch_name}")

            # MERGE (m:Message)-[:IN_CHANNEL]->(c:Channel)
            q = (
                f"MERGE (m:Message {{"
                f"id: {doc_id_int}, "
                f"document_id: '{safe_doc_id}', "
                f"source: '{safe_source}', "
                f"source_id: '{safe_source_id}', "
                f"title: '{safe_title}'"
                f"}})-[:IN_CHANNEL {{id: {edge_id}}}]->"
                f"(c:Channel {{"
                f"id: {ch_id_int}, "
                f"name: '{safe_ch}'"
                f"}})"
            )
            statements.append(q)

        elif record.source == "linear":
            proj_name = record.project or "GENERAL"
            safe_proj = escape_cypher(proj_name)
            proj_id_int = stable_id("project", safe_proj)
            edge_id = stable_id("edge_part_of", f"{record.document_id}->{proj_name}")

            # MERGE (i:Issue)-[:PART_OF]->(p:Project)
            q = (
                f"MERGE (i:Issue {{"
                f"id: {doc_id_int}, "
                f"document_id: '{safe_doc_id}', "
                f"source: '{safe_source}', "
                f"source_id: '{safe_source_id}', "
                f"key: '{safe_source_id}', "
                f"title: '{safe_title}'"
                f"}})-[:PART_OF {{id: {edge_id}}}]->"
                f"(p:Project {{"
                f"id: {proj_id_int}, "
                f"name: '{safe_proj}'"
                f"}})"
            )
            statements.append(q)

        elif record.source == "github":
            repo_name = record.repository or "core-repo"
            safe_repo = escape_cypher(repo_name)
            repo_id_int = stable_id("repository", safe_repo)
            edge_id = stable_id("edge_targets", f"{record.document_id}->{repo_name}")

            # MERGE (pr:PullRequest)-[:TARGETS]->(r:Repository)
            q = (
                f"MERGE (pr:PullRequest {{"
                f"id: {doc_id_int}, "
                f"document_id: '{safe_doc_id}', "
                f"source: '{safe_source}', "
                f"source_id: '{safe_source_id}', "
                f"pr_number: '{safe_source_id}', "
                f"title: '{safe_title}'"
                f"}})-[:TARGETS {{id: {edge_id}}}]->"
                f"(r:Repository {{"
                f"id: {repo_id_int}, "
                f"name: '{safe_repo}'"
                f"}})"
            )
            statements.append(q)

        # 2. Authorship Relationship (Person -[:AUTHORED]-> Document)
        if record.author:
            safe_author = escape_cypher(record.author)
            author_id_int = stable_id("person", safe_author)
            auth_edge_id = stable_id("edge_authored", f"{safe_author}->{record.document_id}")

            doc_label = "Message" if record.source == "slack" else ("Issue" if record.source == "linear" else "PullRequest")

            q_auth = (
                f"MERGE (p:Person {{"
                f"id: {author_id_int}, "
                f"name: '{safe_author}'"
                f"}})-[:AUTHORED {{id: {auth_edge_id}}}]->"
                f"(d:{doc_label} {{"
                f"id: {doc_id_int}, "
                f"document_id: '{safe_doc_id}', "
                f"source: '{safe_source}'"
                f"}})"
            )
            statements.append(q_auth)

        # 3. Explicit Mentions Relationships (Document -[:MENTIONS]-> Entity)
        doc_label = "Message" if record.source == "slack" else ("Issue" if record.source == "linear" else "PullRequest")
        for ref in record.external_refs:
            safe_ref = escape_cypher(ref)
            entity_id_int = stable_id("entity", safe_ref)
            ment_edge_id = stable_id("edge_mentions", f"{record.document_id}->{safe_ref}")

            q_ment = (
                f"MERGE (d:{doc_label} {{"
                f"id: {doc_id_int}, "
                f"document_id: '{safe_doc_id}', "
                f"source: '{safe_source}'"
                f"}})-[:MENTIONS {{id: {ment_edge_id}}}]->"
                f"(e:Entity {{"
                f"id: {entity_id_int}, "
                f"name: '{safe_ref}'"
                f"}})"
            )
            statements.append(q_ment)

        return statements

    def write_records(
        self,
        records: Sequence[CanonicalRecord],
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """
        Execute or dry-run ingestion of canonical records.
        """
        all_statements: list[str] = []
        for rec in records:
            all_statements.extend(self.generate_merge_statements(rec))

        executed_count = 0
        if not dry_run:
            for stmt in all_statements:
                self.query_fn(stmt)
                executed_count += 1

        return {
            "total_records": len(records),
            "total_statements_generated": len(all_statements),
            "dry_run": dry_run,
            "statements_executed": executed_count,
            "sample_statements": all_statements[:5],
        }
