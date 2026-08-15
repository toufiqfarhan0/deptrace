from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


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


@dataclass(frozen=True)
class SemanticEntity:
    type: EntityType
    name: str
    confidence: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Entity name cannot be empty.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Entity confidence must be between 0 and 1."
            )


@dataclass(frozen=True)
class SemanticStatement:
    text: str
    type: StatementType
    confidence: float

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Statement text cannot be empty.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Statement confidence must be between 0 and 1."
            )


@dataclass
class SemanticExtraction:
    message_id: int
    document_id: str
    entities: list[SemanticEntity] = field(
        default_factory=list
    )
    statements: list[SemanticStatement] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if self.message_id < 0:
            raise ValueError(
                "message_id must be non-negative."
            )

        if not self.document_id.strip():
            raise ValueError(
                "document_id cannot be empty."
            )