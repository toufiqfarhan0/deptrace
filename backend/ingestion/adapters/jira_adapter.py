"""
Jira Source Adapter for Veridex (Track 01: Enterprise Sources).

Parses enterprise Jira issue exports into CanonicalRecord instances.
"""

from __future__ import annotations

import re
from typing import Any

from backend.ingestion.adapters.base import BaseAdapter
from backend.ingestion.canonical import CanonicalRecord
from backend.ingestion.references import extract_explicit_references


class JiraAdapter(BaseAdapter):
    """Adapter for enterprise Jira issue exports."""

    @property
    def source_name(self) -> str:
        return "jira"

    def parse_content(self, filename: str, content: str) -> CanonicalRecord:
        document_id = self.extract_dsid(filename)

        # Extract issue key from filename: dsid_xxx__JIRA-4029-slug.txt
        issue_key = ""
        project = "JIRA"
        m_slug = re.match(r"dsid_[a-f0-9]+__([A-Z]{2,10}-\d+)(?:-(.*))?\.txt", filename)
        if m_slug:
            issue_key = m_slug.group(1)
            project = issue_key.split("-")[0]
        else:
            # Fallback search inside text
            m_key = re.search(r"\b([A-Z]{2,10}-\d+)\b", content)
            issue_key = m_key.group(1) if m_key else document_id
            project = issue_key.split("-")[0] if "-" in issue_key else "JIRA"

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        title = lines[0] if lines else f"Jira Issue {issue_key}"

        # Parse Jira metadata fields like Priority, Assignee, Reporter, Status, Sprint, Component
        metadata_map: dict[str, str] = {}
        participants: list[str] = []
        primary_author = None
        primary_timestamp = None

        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}Z)?)\b", content)
        if date_match:
            primary_timestamp = date_match.group(1)

        for line in lines:
            if ":" in line:
                key_part, val_part = line.split(":", 1)
                k_norm = key_part.strip().lower()
                v_norm = val_part.strip()
                if k_norm in {"assignee", "reporter", "created by", "author", "engineer"}:
                    if v_norm and v_norm not in participants:
                        participants.append(v_norm)
                    if primary_author is None and v_norm:
                        primary_author = v_norm
                elif k_norm in {"priority", "status", "sprint", "component", "epic", "fix version", "severity"}:
                    metadata_map[k_norm] = v_norm

        # Extract external cross-references (PRs, Slack channels, related issues)
        ref_items = extract_explicit_references(content)
        ext_refs = sorted(list({r.ref_value for r in ref_items if r.ref_value != issue_key}))

        return CanonicalRecord(
            source=self.source_name,
            source_id=issue_key,
            document_id=document_id,
            record_type="ticket",
            title=f"[{issue_key}] {title}",
            content=content,
            author=primary_author or "jira-automation",
            participants=participants,
            project=project,
            issue_key=issue_key,
            external_refs=ext_refs,
            timestamp=primary_timestamp,
            metadata={
                "issue_key": issue_key,
                "project": project,
                "priority": metadata_map.get("priority", "High"),
                "status": metadata_map.get("status", "Resolved"),
                "sprint": metadata_map.get("sprint", "Current Sprint"),
                "component": metadata_map.get("component", "core-infrastructure"),
                "attributes": metadata_map,
            },
        )
