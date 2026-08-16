"""
Data models for HydraDB Deterministic Retrieval Layer (Step 7).
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Retrieval query request model."""

    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query string cannot be empty or whitespace only.")
        return v


class EvidenceItem(BaseModel):
    """Structured evidence item retrieved from the HydraDB semantic graph."""

    message_id: int = Field(ge=0)
    document_id: str = Field(default="")
    entity_name: str | None = None
    entity_type: str | None = None
    statement: str | None = None
    statement_type: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    relationship: str | None = None
    source: str = "hydradb"
    match_type: str = "exact"  # exact_entity | exact_statement | partial_entity | partial_statement


class RetrievalResponse(BaseModel):
    """Structured response containing retrieved evidence items."""

    query: str
    results: list[EvidenceItem] = Field(default_factory=list)
    result_count: int = 0
