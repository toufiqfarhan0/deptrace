"""
GitHub Source Adapter for Veridex (Step 13B).

Parses plain text GitHub Pull Request exports into CanonicalRecord instances.
"""

from __future__ import annotations

import re
from typing import Any

from backend.ingestion.adapters.base import BaseAdapter
from backend.ingestion.canonical import CanonicalRecord
from backend.ingestion.references import extract_explicit_references


class GitHubAdapter(BaseAdapter):
    """Adapter for GitHub pull request exports."""

    @property
    def source_name(self) -> str:
        return "github"

    def parse_content(self, filename: str, content: str) -> CanonicalRecord:
        document_id = self.extract_dsid(filename)

        # Extract PR number from filename: dsid_xxx__pr-12345-slug.txt
        pr_number = ""
        m_slug = re.match(r"dsid_[a-f0-9]+__pr-(\d+)(?:-(.*))?\.txt", filename)
        if m_slug:
            pr_number = f"PR-{m_slug.group(1)}"
            repo_slug = m_slug.group(2) or ""
        else:
            pr_number = document_id
            repo_slug = ""

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        title = lines[0] if lines else f"GitHub Pull Request {pr_number}"

        # Extract reviewers and commenters: lines starting with 'Name:'
        review_comments: list[dict[str, Any]] = []
        participants: list[str] = []
        primary_author = None
        primary_timestamp = None

        comment_pattern = re.compile(r"^([A-Z][a-zA-Z0-9_\-]+):\s*(.*)$")
        timestamp_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

        for line in lines[1:]:
            m_comm = comment_pattern.match(line)
            if m_comm:
                author_name = m_comm.group(1).strip()
                comment_text = m_comm.group(2).strip()

                # Filter out standard section headers that end in colon (like 'Context:', 'Motivation:', 'Checklist:')
                if author_name.lower() in {
                    "context",
                    "motivation",
                    "summary",
                    "checklist",
                    "impact",
                    "related",
                    "notes",
                    "coverage",
                    "verification",
                    "changes",
                    "goal",
                    "scope",
                }:
                    continue

                if author_name not in participants:
                    participants.append(author_name)
                if primary_author is None:
                    primary_author = author_name

                review_comments.append({
                    "author": author_name,
                    "comment": comment_text[:160],
                })

            if primary_timestamp is None:
                ts_m = timestamp_pattern.search(line)
                if ts_m:
                    primary_timestamp = ts_m.group(1)

        # Inferred repository or component name from slug
        inferred_repo = repo_slug.split("-")[0] if repo_slug else "core-repo"

        # External cross-references
        ref_items = extract_explicit_references(content)
        ext_refs = sorted(list({r.ref_value for r in ref_items if r.ref_value != pr_number}))

        return CanonicalRecord(
            source=self.source_name,
            source_id=pr_number,
            document_id=document_id,
            record_type="pull_request",
            title=f"[{pr_number}] {title}",
            content=content,
            author=primary_author,
            participants=participants,
            repository=inferred_repo,
            external_refs=ext_refs,
            timestamp=primary_timestamp,
            metadata={
                "pr_number": pr_number,
                "repository": inferred_repo,
                "review_comment_count": len(review_comments),
                "review_comments": review_comments,
            },
        )
