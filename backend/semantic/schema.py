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

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Statement text cannot be empty."
            )

        return value


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