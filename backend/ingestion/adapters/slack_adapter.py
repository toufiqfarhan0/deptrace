"""
Slack Source Adapter for Veridex (Step 13B).

Parses plain text Slack conversation dumps into CanonicalRecord instances.
"""

from __future__ import annotations

import re
from typing import Any

from backend.ingestion.adapters.base import BaseAdapter
from backend.ingestion.canonical import CanonicalRecord
from backend.ingestion.references import extract_explicit_references


class SlackAdapter(BaseAdapter):
    """Adapter for Slack conversation exports."""

    @property
    def source_name(self) -> str:
        return "slack"

    def parse_content(self, filename: str, content: str) -> CanonicalRecord:
        document_id = self.extract_dsid(filename)

        # Extract thread ID from filename slug e.g. dsid_00193d...__3287654321-waitlisting...
        thread_id = ""
        m_slug = re.match(r"dsid_[a-f0-9]+__(\d+)(?:-(.*))?\.txt", filename)
        if m_slug:
            thread_id = m_slug.group(1)
            title_slug = m_slug.group(2) or ""
        else:
            thread_id = document_id
            title_slug = ""

        lines = content.splitlines()
        channel = lines[0].strip() if lines else "general"

        # Find all message authors: 'handle (role):' or 'handle:'
        participants: list[str] = []
        messages_meta: list[dict[str, Any]] = []
        primary_author = None
        primary_timestamp = None

        # Regex matching Slack message turns: e.g. 'alex (support):', '`tess_acme (Customer):`', 'sam:'
        author_pattern = re.compile(
            r"^(?:`|)?([a-zA-Z0-9_\-\.]+)(?:\s*\((.*?)\))?(?:`|)?\s*:\s*(.*)$"
        )
        timestamp_pattern = re.compile(
            r"\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)\]"
        )

        for line in lines[1:]:
            line_str = line.strip()
            if not line_str:
                continue

            match = author_pattern.match(line_str)
            if match:
                handle = match.group(1).lower()
                role = (match.group(2) or "").lower()
                body = match.group(3)

                if handle not in participants:
                    participants.append(handle)
                if primary_author is None:
                    primary_author = handle

                messages_meta.append({
                    "author": handle,
                    "role": role if role else None,
                    "preview": body[:120],
                })

            # Check for embedded log timestamps
            if primary_timestamp is None:
                ts_m = timestamp_pattern.search(line_str)
                if ts_m:
                    primary_timestamp = ts_m.group(1)

        # Title: channel + slug
        if title_slug:
            clean_title = f"#{channel}: {title_slug.replace('-', ' ').title()}"
        else:
            first_msg = messages_meta[0]["preview"] if messages_meta else "Conversation"
            clean_title = f"#{channel}: {first_msg[:60]}"

        # External cross-references
        ref_items = extract_explicit_references(content)
        ext_refs = sorted(list({r.ref_value for r in ref_items}))

        return CanonicalRecord(
            source=self.source_name,
            source_id=thread_id,
            document_id=document_id,
            record_type="conversation",
            title=clean_title,
            content=content,
            author=primary_author,
            participants=participants,
            channel=channel,
            external_refs=ext_refs,
            timestamp=primary_timestamp,
            metadata={
                "channel": channel,
                "thread_id": thread_id,
                "message_count": len(messages_meta),
                "participants": participants,
            },
        )
