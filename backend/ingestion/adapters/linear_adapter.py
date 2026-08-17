"""
Linear Source Adapter for Veridex (Step 13B).

Parses plain text Linear issue exports into CanonicalRecord instances.
"""

from __future__ import annotations

import re
from typing import Any

from backend.ingestion.adapters.base import BaseAdapter
from backend.ingestion.canonical import CanonicalRecord
from backend.ingestion.references import extract_explicit_references


class LinearAdapter(BaseAdapter):
    """Adapter for Linear issue exports."""

    @property
    def source_name(self) -> str:
        return "linear"

    def parse_content(self, filename: str, content: str) -> CanonicalRecord:
        document_id = self.extract_dsid(filename)

        # Extract issue key from filename: dsid_xxx__ENG-1234-slug.txt
        issue_key = ""
        project = "GENERAL"
        m_slug = re.match(r"dsid_[a-f0-9]+__([A-Z]{2,6}-\d+)(?:-(.*))?\.txt", filename)
        if m_slug:
            issue_key = m_slug.group(1)
            project = issue_key.split("-")[0]
        else:
            issue_key = document_id

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        title = lines[0] if lines else f"Linear Issue {issue_key}"

        # Extract structured timeline entries: e.g. "2026-02-21 - Aisha Patel: Kicked off design doc."
        timeline_entries: list[dict[str, Any]] = []
        participants: list[str] = []
        primary_author = None
        primary_timestamp = None

        timeline_pattern = re.compile(
            r"^(\d{4}-\d{2}-\d{2})\s*-\s*([^:]+):\s*(.*)$"
        )

        for line in lines:
            m_time = timeline_pattern.match(line)
            if m_time:
                date_str = m_time.group(1)
                actor_raw = m_time.group(2).strip()
                note = m_time.group(3).strip()

                if primary_timestamp is None:
                    primary_timestamp = date_str

                # Parse actor names (e.g. 'Aisha Patel' or 'Architecture sync (Marco Alvarez, Lena Cho)')
                names_to_parse: list[str] = []
                paren_match = re.search(r"\((.*?)\)", actor_raw)
                if paren_match:
                    names_to_parse.extend([n.strip() for n in re.split(r",|\band\b", paren_match.group(1)) if n.strip()])
                else:
                    names_to_parse.extend([n.strip() for n in re.split(r",|\band\b", actor_raw) if n.strip()])

                for actor in names_to_parse:
                    clean_actor = re.sub(r"[()]", "", actor).strip()
                    if clean_actor and clean_actor not in participants:
                        participants.append(clean_actor)
                    if primary_author is None and clean_actor:
                        primary_author = clean_actor

                timeline_entries.append({
                    "date": date_str,
                    "actors": names_to_parse,
                    "note": note[:160],
                })

        # Extract external cross-references
        ref_items = extract_explicit_references(content)
        ext_refs = sorted(list({r.ref_value for r in ref_items if r.ref_value != issue_key}))

        return CanonicalRecord(
            source=self.source_name,
            source_id=issue_key,
            document_id=document_id,
            record_type="issue",
            title=f"[{issue_key}] {title}",
            content=content,
            author=primary_author,
            participants=participants,
            project=project,
            issue_key=issue_key,
            external_refs=ext_refs,
            timestamp=primary_timestamp,
            metadata={
                "issue_key": issue_key,
                "project": project,
                "timeline_count": len(timeline_entries),
                "timeline": timeline_entries,
            },
        )
