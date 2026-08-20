"""
Cross-Source Reference Extractor & Deterministic Entity Resolution (Step 13B).

Extracts explicit identifiers (issue keys, PR numbers, user mentions) across
Slack, Linear, and GitHub without LLM inference.
"""

from __future__ import annotations

import re
from typing import NamedTuple, Optional
from pydantic import BaseModel, Field

# Valid enterprise issue key prefixes observed in EnterpriseRAG-Bench
VALID_ISSUE_PREFIXES = {
    "ENG",
    "PM",
    "DES",
    "INC",
    "REL",
    "SUP",
    "SEC",
    "INF",
    "MET",
    "PN",
    "LEG",
    "CR",
    "INV",
    "DX",
    "JIRA",
    "RFC",
    "ADR",
    "CONF",
}

# Known common ambiguous single names that require qualifier/handle to resolve
AMBIGUOUS_NAMES = {
    "alex",
    "sam",
    "maria",
    "sara",
    "mike",
    "john",
    "dan",
    "david",
    "chris",
    "ben",
    "tom",
}


class ReferenceItem(BaseModel):
    """Extracted cross-source reference token."""

    ref_type: str = Field(..., description="'issue' | 'pr' | 'user' | 'component'")
    ref_value: str = Field(..., description="Normalized reference identifier")
    raw_token: str = Field(..., description="Original text token")


class EntityResolutionResult(BaseModel):
    """Deterministic entity resolution result."""

    canonical_name: str
    source: str
    source_identifier: str
    is_ambiguous: bool
    confidence: float
    resolution_method: str


def extract_explicit_references(text: str) -> list[ReferenceItem]:
    """
    Extract explicit, deterministic reference tokens from raw text.
    Filters out noise like 'UTF-8', 'HTTP-2', etc.
    """
    if not text:
        return []

    refs: list[ReferenceItem] = []
    seen: set[tuple[str, str]] = set()

    # 1. Issue Keys (e.g., ENG-4821, INC-2026, REL-311, SUP-18436)
    for m in re.finditer(r"\b([A-Z]{2,6})-(\d{1,7})\b", text):
        prefix, num = m.group(1), m.group(2)
        if prefix in VALID_ISSUE_PREFIXES:
            val = f"{prefix}-{num}"
            if ("issue", val) not in seen:
                seen.add(("issue", val))
                refs.append(
                    ReferenceItem(
                        ref_type="issue",
                        ref_value=val,
                        raw_token=m.group(0),
                    )
                )

    # 2. GitHub PR References (e.g., PR #99501, PR 99501, pr-99501, #99501, PR-99501)
    for m in re.finditer(r"\b(?:PR\s*#?|pr-|PR-|#)(\d{2,7})\b", text, re.IGNORECASE):
        val = f"PR-{m.group(1)}"
        if ("pr", val) not in seen:
            seen.add(("pr", val))
            refs.append(
                ReferenceItem(
                    ref_type="pr",
                    ref_value=val,
                    raw_token=m.group(0),
                )
            )

    # 3. User Mentions (e.g., @omar, @aisha_patel, @alex)
    for m in re.finditer(r"@([a-zA-Z0-9_\-\.]+)", text):
        handle = m.group(1).lower().rstrip(".")
        if len(handle) >= 2 and ("user", handle) not in seen:
            seen.add(("user", handle))
            refs.append(
                ReferenceItem(
                    ref_type="user",
                    ref_value=handle,
                    raw_token=m.group(0),
                )
            )

    return refs


def resolve_person_identity(
    raw_name_or_handle: str,
    source: str,
    role_or_context: Optional[str] = None,
) -> EntityResolutionResult:
    """
    Deterministically resolve person identities across sources.
    Conservative: if a single common first name lacks full name or unique handle,
    mark it ambiguous with lower confidence to prevent false positive identity merges.
    """
    cleaned = raw_name_or_handle.strip().lstrip("@")
    norm = cleaned.lower()

    # If full name (e.g., 'Aisha Patel', 'Marco Alvarez') -> high confidence
    if " " in cleaned:
        return EntityResolutionResult(
            canonical_name=cleaned,
            source=source,
            source_identifier=cleaned,
            is_ambiguous=False,
            confidence=0.95,
            resolution_method="exact_full_name",
        )

    # If handle with role/context (e.g. 'sam (eng-runtime)', 'alex (support)')
    if role_or_context and role_or_context.strip().lower() not in {"", "none"}:
        canonical = f"{norm} ({role_or_context.strip().lower()})"
        return EntityResolutionResult(
            canonical_name=canonical,
            source=source,
            source_identifier=raw_name_or_handle,
            is_ambiguous=False,
            confidence=0.85,
            resolution_method="scoped_role_handle",
        )

    # If ambiguous common single name without qualification
    if norm in AMBIGUOUS_NAMES:
        return EntityResolutionResult(
            canonical_name=norm,
            source=source,
            source_identifier=raw_name_or_handle,
            is_ambiguous=True,
            confidence=0.40,
            resolution_method="unqualified_single_name",
        )

    # Otherwise unambiguous handle/name
    return EntityResolutionResult(
        canonical_name=norm,
        source=source,
        source_identifier=raw_name_or_handle,
        is_ambiguous=False,
        confidence=0.75,
        resolution_method="normalized_handle",
    )
