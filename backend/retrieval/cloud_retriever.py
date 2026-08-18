"""
HydraDB Cloud v2 Knowledge Retrieval Adapter (Step 17D).

Performs hybrid graph-augmented retrieval over HydraDB Cloud v2 (https://api.hydradb.com),
maps raw Cloud chunks into normalized Veridex EvidenceItem instances, and enforces
strict provenance and identifier-aware matching.
"""

from __future__ import annotations

import os
import re
import sys
import time
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

from backend.retrieval.models import EvidenceItem, RetrievalResponse
from backend.semantic.ids import stable_id


class HydraCloudRetriever:
    """
    Retrieval adapter for HydraDB Cloud v2 API.
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
            "Content-Type": "application/json",
        }

    def check_health(self) -> dict[str, Any]:
        """Verify HydraDB Cloud connectivity and database status without leaking API key."""
        if not self.api_key:
            return {"status": "degraded", "hydradb": "unconfigured: HYDRA_DB_API_KEY missing"}

        try:
            res = requests.get(
                f"{self.base_url}/databases/status",
                headers={"Authorization": f"Bearer {self.api_key}", "API-Version": "2"},
                params={"database": self.database},
                timeout=10,
            )
            if res.ok:
                data = res.json().get("data", {})
                infra = data.get("infra", {})
                if infra.get("ready_for_ingestion", False) or data.get("database") == self.database:
                    return {"status": "ok", "hydradb": "ok (cloud: veridex-hackhydra)"}
            return {"status": "degraded", "hydradb": f"unexpected_response: HTTP {res.status_code}"}
        except Exception as exc:
            return {"status": "degraded", "hydradb": f"unreachable: {type(exc).__name__}"}

    def clean_chunk_text(self, raw: str) -> str:
        """
        Unpack clean human-readable text from HydraDB Cloud chunk payloads.
        Handles complete JSON structures, truncated JSON fragments, and raw text.
        """
        if not raw:
            return ""

        # 1. Complete valid JSON object
        if raw.startswith("{") and raw.endswith("}"):
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    if "content" in data and isinstance(data["content"], dict):
                        txt = data["content"].get("text", "")
                        if txt:
                            return str(txt).strip()
                    if "content" in data and isinstance(data["content"], str):
                        return data["content"].strip()
                    if "text" in data and isinstance(data["text"], str):
                        return data["text"].strip()
            except Exception:
                pass

        # 2. JSON fragment containing "content":{"text":"..."}
        match_content_text = re.search(r'"content"\s*:\s*\{\s*"text"\s*:\s*"(.*?)(?:",\s*"|"\s*\}|$)', raw, re.DOTALL)
        if match_content_text:
            raw_inner = match_content_text.group(1)
            try:
                return json.loads(f'"{raw_inner}"').strip()
            except Exception:
                return (
                    raw_inner.replace(r"\n", "\n")
                    .replace(r"\"", '"')
                    .replace(r"\u003e", ">")
                    .replace(r"\u003c", "<")
                    .strip()
                )

        # 3. JSON fragment containing "text":"..."
        match_text = re.search(r'"text"\s*:\s*"(.*?)(?:",\s*"|"\s*\}|$)', raw, re.DOTALL)
        if match_text:
            raw_inner = match_text.group(1)
            try:
                return json.loads(f'"{raw_inner}"').strip()
            except Exception:
                return (
                    raw_inner.replace(r"\n", "\n")
                    .replace(r"\"", '"')
                    .replace(r"\u003e", ">")
                    .replace(r"\u003c", "<")
                    .strip()
                )

        # 4. Plain text containing trailing JSON metadata artifacts
        cleaned = re.sub(r'",\s*"(?:html_base64|csv_base64|markdown|files|layout|tenant_metadata|document).*$', '', raw, flags=re.DOTALL)
        return cleaned.strip()

    def extract_identifiers(self, query: str) -> list[str]:
        """Extract explicit technical identifiers, ticket keys, and incident names."""
        tokens: list[str] = []
        # Pattern 1: Ticket / PR / Incident keys like PR-99501, ENG-30521, INC-2026, DES-23981, PM-352917
        key_matches = re.findall(r"\b([A-Z]{2,6}-\d{2,7})\b", query)
        tokens.extend(key_matches)
        # Pattern 2: Numeric Slack timestamps/IDs (10-digit)
        slack_matches = re.findall(r"\b(\d{10})\b", query)
        tokens.extend(slack_matches)
        # Pattern 3: Channel names e.g. #incidents, #eng-runtime, #eng-security
        channel_matches = re.findall(r"(#[a-z0-9\-_]+)", query, re.IGNORECASE)
        tokens.extend(channel_matches)
        # Pattern 4: Key known entities and incident subjects
        keywords = [
            "Bluecrest",
            "KMS",
            "guardrails",
            "overload",
            "tokenizer",
            "cgroup",
            "interop",
            "deferred-indexing",
        ]
        q_lower = query.lower()
        for kw in keywords:
            if kw.lower() in q_lower:
                tokens.append(kw)
        return list(dict.fromkeys(tokens))

    def retrieve(self, query: str, limit: int = 10) -> RetrievalResponse:
        """
        Execute knowledge query against HydraDB Cloud v2.
        Maps raw Cloud chunks into normalized Veridex EvidenceItem list with full text preservation.
        """
        q_clean = query.strip()
        if not q_clean:
            return RetrievalResponse(query=query, results=[], result_count=0)

        headers = self.get_headers()
        payload = {
            "database": self.database,
            "query": q_clean,
            "type": "knowledge",
            "query_by": "hybrid",
            "mode": "thinking",
            "graph_context": True,
            "query_forceful_relations": True,
            "max_results": limit,
        }

        try:
            res = requests.post(f"{self.base_url}/query", headers=headers, json=payload, timeout=30)
        except Exception as exc:
            print(f"HydraDB Cloud query failed: {exc}", file=sys.stderr)
            return RetrievalResponse(query=query, results=[], result_count=0)

        if not res.ok:
            print(f"HydraDB Cloud query returned HTTP {res.status_code}: {res.text}", file=sys.stderr)
            return RetrievalResponse(query=query, results=[], result_count=0)

        res_json = res.json()
        data = res_json.get("data", {})
        chunks = data.get("chunks", [])

        explicit_ids = self.extract_identifiers(q_clean)
        evidence_items: list[EvidenceItem] = []

        for chunk in chunks:
            chunk_id = chunk.get("id", "")
            meta = chunk.get("additional_metadata", {})
            veridex_doc_id = meta.get("veridex_document_id") or chunk_id
            veridex_src_id = meta.get("veridex_source_id") or chunk.get("source_title", "")
            veridex_canon_id = meta.get("veridex_canonical_id")
            source_type = chunk.get("source_type") or meta.get("source") or "cloud"

            # Parse integer message ID anchor
            try:
                msg_id = int(veridex_canon_id) if veridex_canon_id else stable_id("cloud", veridex_doc_id)
            except (ValueError, TypeError):
                msg_id = stable_id("cloud", veridex_doc_id)

            raw_content = chunk.get("chunk_content", "")
            cleaned_content = self.clean_chunk_text(raw_content)

            # Statement and entity extraction with full text preservation
            title = chunk.get("source_title", "")
            author = meta.get("author") or "unknown"
            statement_snippet = f"({veridex_src_id}) {title}: {cleaned_content[:1500]}".strip()

            relevancy = float(chunk.get("relevancy_score", 1.0))
            # Normalize confidence to [0.0, 1.0]
            conf = min(max(relevancy if relevancy <= 1.0 else 1.0, 0.0), 1.0)

            # Match type determination
            matched_id = None
            is_exact = False
            for ident in explicit_ids:
                if (
                    ident.lower() in veridex_src_id.lower()
                    or ident.lower() in title.lower()
                    or ident.lower() in cleaned_content.lower()
                ):
                    matched_id = ident
                    is_exact = True
                    break

            match_type = "exact" if is_exact else "semantic"
            entity_name = matched_id or veridex_src_id or title

            item = EvidenceItem(
                message_id=msg_id,
                document_id=veridex_doc_id,
                entity_name=entity_name,
                entity_type=source_type,
                statement=statement_snippet,
                statement_type="fact" if "PR" in str(veridex_src_id) or "ENG" in str(veridex_src_id) else "action",
                confidence=conf,
                relationship="KNOWLEDGE_SOURCE",
                source="hydradb_cloud",
                match_type=match_type,
            )
            evidence_items.append(item)

        # Prioritize exact identifier matches at the top of results
        if explicit_ids:
            evidence_items.sort(key=lambda item: 0 if item.match_type == "exact" else 1)

        return RetrievalResponse(
            query=query,
            results=evidence_items[:limit],
            result_count=len(evidence_items[:limit]),
        )
