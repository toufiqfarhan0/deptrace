"""
Confluence Source Adapter for Veridex (Track 01: Enterprise Sources).

Parses enterprise Confluence pages, RFCs, and Architecture Decision Records (ADRs).
"""

from __future__ import annotations

import re
from typing import Any

from backend.ingestion.adapters.base import BaseAdapter
from backend.ingestion.canonical import CanonicalRecord
from backend.ingestion.references import extract_explicit_references


class ConfluenceAdapter(BaseAdapter):
    """Adapter for Confluence RFCs, specs, and Architecture Decision Records."""

    @property
    def source_name(self) -> str:
        return "confluence"

    def parse_content(self, filename: str, content: str) -> CanonicalRecord:
        document_id = self.extract_dsid(filename)

        # Extract RFC or Page key (e.g. RFC-881, ADR-104, CONF-204)
        m_rfc = re.search(r"\b(RFC-\d+|ADR-\d+|CONF-\d+|DOC-\d+)\b", content)
        doc_key = m_rfc.group(1) if m_rfc else document_id

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        title = lines[0] if lines else f"Confluence RFC {doc_key}"

        # Extract RFC metadata: Status (APPROVED/PROPOSED), Author, Reviewers, Decisions
        rfc_status = "APPROVED"
        primary_author = None
        participants: list[str] = []
        primary_timestamp = None

        m_date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", content)
        if m_date:
            primary_timestamp = m_date.group(1)

        for line in lines:
            if ":" in line:
                key_part, val_part = line.split(":", 1)
                k_norm = key_part.strip().lower()
                v_norm = val_part.strip()
                if k_norm in {"status", "state", "decision"}:
                    if "approved" in v_norm.lower():
                        rfc_status = "APPROVED"
                    elif "proposed" in v_norm.lower():
                        rfc_status = "PROPOSED"
                    elif "deprecated" in v_norm.lower() or "superseded" in v_norm.lower():
                        rfc_status = "SUPERSEDED"
                    else:
                        rfc_status = v_norm
                elif k_norm in {"author", "owner", "created by", "lead architect"}:
                    if v_norm and v_norm not in participants:
                        participants.append(v_norm)
                    if primary_author is None and v_norm:
                        primary_author = v_norm
                elif k_norm in {"reviewers", "stakeholders", "attendees"}:
                    for p in re.split(r",|\band\b", v_norm):
                        p_clean = p.strip()
                        if p_clean and p_clean not in participants:
                            participants.append(p_clean)

        # Extract external cross-references (PRs, Tickets, Incidents)
        ref_items = extract_explicit_references(content)
        ext_refs = sorted(list({r.ref_value for r in ref_items if r.ref_value != doc_key}))

        return CanonicalRecord(
            source=self.source_name,
            source_id=doc_key,
            document_id=document_id,
            record_type="doc",
            title=f"[{doc_key}] {title}",
            content=content,
            author=primary_author or "architecture-team",
            participants=participants,
            project="ARCHITECTURE",
            issue_key=doc_key,
            external_refs=ext_refs,
            timestamp=primary_timestamp,
            metadata={
                "rfc_id": doc_key,
                "status": rfc_status,
                "category": "Architecture Decision Record",
                "space": "ENGINEERING-RFC",
            },
        )
