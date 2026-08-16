from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


EntityType = Literal[
    "Customer",
    "Project",
    "Incident",
    "Decision",
    "ConfigurationChange",
    "Entity",
]

StatementType = Literal[
    "fact",
    "decision",
    "claim",
    "action",
    "outcome",
]


class SemanticEntity(BaseModel):
    type: EntityType
    name: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Entity name cannot be empty."
            )

        return value


class SemanticStatement(BaseModel):
    text: str = Field(min_length=1)
    type: StatementType
    confidence: float = Field(ge=0.0, le=1.0)
    entity_refs: list[str] = Field(default_factory=list)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Statement text cannot be empty."
            )

        return value

    @field_validator("entity_refs")
    @classmethod
    def validate_entity_refs(cls, refs: list[str]) -> list[str]:
        cleaned_refs: list[str] = []
        seen: set[str] = set()

        for ref in refs:
            if not isinstance(ref, str):
                continue
            normalized = ref.strip()
            if not normalized:
                continue
            if normalized not in seen:
                seen.add(normalized)
                cleaned_refs.append(normalized)

        return cleaned_refs


class SemanticExtraction(BaseModel):
    message_id: int = Field(ge=0)
    document_id: str = Field(min_length=1)

    entities: list[SemanticEntity] = Field(
        default_factory=list
    )

    statements: list[SemanticStatement] = Field(
        default_factory=list
    )

    @field_validator("document_id")
    @classmethod
    def validate_document_id(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "document_id cannot be empty."
            )

        return value