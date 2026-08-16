"""
Data models for Graph RAG Answer Generation layer (Step 8).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.retrieval.models import EvidenceItem
except ImportError:
    from models import EvidenceItem  # type: ignore[no-redef]


class AnswerRequest(BaseModel):
    """Request model for Graph RAG question answering."""

    question: str = Field(min_length=1)
    retrieval_limit: int = Field(default=10, ge=1, le=100)

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question string cannot be empty or whitespace only.")
        return v


class AnswerResponse(BaseModel):
    """Response model containing generated answer, evidence, and grounding status."""

    question: str
    answer: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: float | None = 1.0
    grounded: bool = False
    cited_evidence_ids: list[str] = Field(default_factory=list)
    error: str | None = None
