"""
Canonical Multi-Source Record Model for Veridex (Step 13B).

Defines the source-independent canonical schema capturing Slack, Linear,
and GitHub enterprise records with strict provenance and deterministic IDs.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field

from backend.semantic.ids import stable_id


class CanonicalRecord(BaseModel):
    """
    Source-independent canonical representation of an enterprise document.
    """

    source: str = Field(
        ...,
        description="Source system name: 'slack' | 'linear' | 'github'",
    )
    source_id: str = Field(
        ...,
        description="Primary identifier within source system (thread_id, issue_key, pr_number)",
    )
    document_id: str = Field(
        ...,
        description="Global dataset document identifier (e.g. dsid_00193d850bed...)",
    )
    record_type: str = Field(
        ...,
        description="Canonical type: 'conversation' | 'issue' | 'pull_request'",
    )
    title: str = Field(
        ...,
        description="Human-readable title or subject line",
    )
    content: str = Field(
        ...,
        description="Full raw text content with provenance intact",
    )
    author: Optional[str] = Field(
        default=None,
        description="Primary author, submitter, or reporter name/handle",
    )
    participants: list[str] = Field(
        default_factory=list,
        description="All unique participants, commenters, reviewers, or mentioned actors",
    )
    channel: Optional[str] = Field(
        default=None,
        description="Slack channel name (e.g. 'incidents', 'eng-runtime')",
    )
    repository: Optional[str] = Field(
        default=None,
        description="GitHub repository or component name",
    )
    project: Optional[str] = Field(
        default=None,
        description="Linear project or team identifier (e.g. 'ENG', 'PM', 'INC')",
    )
    issue_key: Optional[str] = Field(
        default=None,
        description="Linear issue identifier (e.g. 'ENG-68910', 'INC-2026')",
    )
    external_refs: list[str] = Field(
        default_factory=list,
        description="Explicit cross-source references (e.g. ['INC-2026', 'ENG-4821', 'PR-99501'])",
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="Observed primary timestamp or date (ISO 8601 or UTC string)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific structured metadata (milestones, review comments, checklists)",
    )

    @property
    def canonical_id(self) -> int:
        """
        Deterministic 63-bit positive integer ID for HydraDB vertices.
        Uses stable_id(namespace=source, value=document_id).
        """
        return stable_id(namespace=self.source, value=self.document_id)

    @property
    def source_key(self) -> str:
        """Namespaced source key for cross-source uniqueness."""
        return f"{self.source}:{self.document_id}"
