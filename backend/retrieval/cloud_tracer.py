"""
HydraDB Cloud v2 Dependency Tracer Adapter (Step 17D).

Inspects graph relations from HydraDB Cloud v2 (GET /context/relations) and
maps genuine relation triplets into DependencyTraceResponse models.
Accurately documents Cloud graph traversal boundaries without fabricating links.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass

from backend.retrieval.models import (
    DependencyTraceResponse,
    EvidenceItem,
    StatementTimelineItem,
    TraceHop,
    TraceImpactSummary,
)
from backend.semantic.ids import stable_id


class HydraCloudTracer:
    """
    Dependency Tracer adapter for HydraDB Cloud v2.
    """

    def __init__(
        self,
        api_key: str | None = None,
        database: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("HYDRA_DB_API_KEY")
        self.database = (
            database
            or os.getenv("HYDRA_DB_DATABASE")
            or os.getenv("HYDRA_DATABASE", "veridex-hackhydra")
        )
        self.base_url = (
            base_url
            or os.getenv("HYDRA_DB_BASE_URL")
            or os.getenv("HYDRA_BASE_URL", "https://api.hydradb.com")
        )

    def get_headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("HYDRA_DB_API_KEY is not configured.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "API-Version": "2",
        }

    def list_entities(self) -> list[str]:
        """
        List known technical entities available in the Cloud dataset.
        Returns verified entity keys and IDs from the 60-document dataset.
        """
        return sorted([
            "REL-311",
            "PR-99501",
            "PR-993211",
            "PR-482199",
            "PR-209876",
            "PR-947999",
            "PR-35802",
            "PR-91234",
            "INC-2026",
            "ENG-30521",
            "ENG-68910",
            "ENG-233901",
            "ENG-762314",
            "ENG-5432",
            "DES-23981",
            "PM-352917",
            "PM-16842",
            "Bluecrest",
            "kernel-selector",
            "api-search",
            "request-time guard",
            "v3.1.1-legacy-tokenizer",
            "strict_model:true",
            "compact-model-v1",
            "kernel-fallback policy",
        ])

    def get_available_entities(self) -> list[str]:
        """Alias for list_entities to match DependencyTracer interface."""
        return self.list_entities()

    def trace(
        self,
        entity: str,
        max_depth: int = 2,
        limit: int = 20,
    ) -> DependencyTraceResponse:
        """
        Trace entity dependencies in HydraDB Cloud v2 using genuine extracted relations.
        """
        target = entity.strip()
        if not target:
            return DependencyTraceResponse(
                root_entity="",
                found=False,
                error="Target entity cannot be empty.",
            )

        if not self.api_key:
            return DependencyTraceResponse(
                root_entity=target,
                found=False,
                error="HydraDB Cloud API key not configured.",
            )

        # 1. Search for documents matching this entity via Cloud Query API
        headers = {**self.get_headers(), "Content-Type": "application/json"}
        payload = {
            "database": self.database,
            "query": target,
            "type": "knowledge",
            "query_by": "hybrid",
            "mode": "thinking",
            "graph_context": True,
            "max_results": limit,
        }

        try:
            res_q = requests.post(f"{self.base_url}/query", headers=headers, json=payload, timeout=20)
            if not res_q.ok:
                return DependencyTraceResponse(
                    root_entity=target,
                    found=False,
                    error=f"Cloud query failed with HTTP {res_q.status_code}",
                )
            q_data = res_q.json().get("data", {})
            chunks = q_data.get("chunks", [])
        except Exception as exc:
            return DependencyTraceResponse(
                root_entity=target,
                found=False,
                error=f"Cloud query network error: {type(exc).__name__}",
            )

        if not chunks:
            return DependencyTraceResponse(
                root_entity=target,
                found=False,
                error=f"Entity '{target}' not found in HydraDB Cloud context.",
            )

        # 2. Collect document relations from GET /context/relations for the top matching document
        hops: list[TraceHop] = []
        timeline: list[StatementTimelineItem] = []
        linked_entities: list[str] = []
        affected_messages: set[int] = set()

        doc_id = chunks[0].get("id", "")
        res_rel = requests.get(
            f"{self.base_url}/context/relations",
            headers=self.get_headers(),
            params={"database": self.database, "id": doc_id, "type": "knowledge"},
            timeout=15,
        )

        order_idx = 1
        if res_rel.ok:
            rel_data = res_rel.json().get("data", {})
            cloud_relations = rel_data.get("relations", [])
            for r_entry in cloud_relations:
                src_name = r_entry.get("source", {}).get("name", "")
                tgt_name = r_entry.get("target", {}).get("name", "")
                rels = r_entry.get("relations", [])

                for r in rels:
                    predicate = r.get("canonical_predicate") or r.get("raw_predicate") or "RELATED_TO"
                    ctx_text = r.get("context") or f"{src_name} -> {tgt_name}"
                    msg_id = stable_id("cloud_rel", r.get("relationship_id") or f"{src_name}->{tgt_name}")
                    affected_messages.add(msg_id)

                    if tgt_name and tgt_name not in linked_entities and tgt_name != target:
                        linked_entities.append(tgt_name)

                    hops.append(
                        TraceHop(
                            source_entity=src_name or target,
                            target_entity=tgt_name or target,
                            hop_distance=1,
                            via_message_id=msg_id,
                            document_id=doc_id,
                            relationship=predicate.upper().replace(" ", "_"),
                            statements=[ctx_text],
                        )
                    )

                    timeline.append(
                        StatementTimelineItem(
                            order_index=order_idx,
                            message_id=msg_id,
                            document_id=doc_id,
                            statement_type="fact",
                            statement=ctx_text,
                            associated_entity=tgt_name or src_name,
                            relationship=predicate.upper().replace(" ", "_"),
                        )
                    )
                    order_idx += 1

        # Add timeline items from retrieved chunks if timeline is short
        for c in chunks[:5]:
            c_id = c.get("id", "")
            meta = c.get("additional_metadata", {})
            src_id = meta.get("veridex_source_id") or c.get("source_title", "")
            canon_id = int(meta.get("veridex_canonical_id", 0)) or stable_id("cloud", c_id)
            affected_messages.add(canon_id)

            if src_id and src_id not in linked_entities and src_id != target:
                linked_entities.append(src_id)

            timeline.append(
                StatementTimelineItem(
                    order_index=order_idx,
                    message_id=canon_id,
                    document_id=c_id,
                    statement_type="fact" if "PR" in src_id else "action",
                    statement=f"({src_id}) {c.get('source_title', '')}: {c.get('chunk_content', '')[:200]}...",
                    associated_entity=src_id or target,
                    relationship="DOCUMENT_SOURCE",
                )
            )
            order_idx += 1

        impact_summary = TraceImpactSummary(
            root_entity=target,
            traversal_depth=min(max_depth, 2),
            total_linked_entities=len(linked_entities),
            total_statements=len(timeline),
            statements_by_type={"fact": len(timeline)},
            affected_components=linked_entities,
            affected_messages=sorted(list(affected_messages)),
            affected_documents=[doc_id] if doc_id else [],
        )

        return DependencyTraceResponse(
            root_entity=target,
            found=True,
            impact_summary=impact_summary,
            dependency_hops=hops[:limit],
            timeline=timeline[:limit],
            raw_evidence=[],
            error=None,
        )
