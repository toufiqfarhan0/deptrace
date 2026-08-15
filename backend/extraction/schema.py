"""
Structured Schema and Provenance Data Models for Semantic Extraction.

Defines target semantic entity types, statement types, and validation models
for extracting unstructured knowledge from Slack messages.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


# Supported Semantic Entity Types
SemanticEntityType = Literal[
    "Customer",
    "Project",
    "Incident",
    "Decision",
    "ConfigurationChange",
    "Entity",
]

KNOWN_ENTITY_TYPES: set[str] = {
    "Customer",
    "Project",
    "Incident",
    "Decision",
    "ConfigurationChange",
    "Entity",
}

# Supported Semantic Statement Types
StatementType = Literal[
    "fact",
    "decision",
    "claim",
    "action",
    "outcome",
]

KNOWN_STATEMENT_TYPES: set[str] = {
    "fact",
    "decision",
    "claim",
    "action",
    "outcome",
}


@dataclass
class SemanticEntity:
    """
    Represents a domain entity extracted from an unstructured message.
    """

    name: str
    type: str
    confidence: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError(f"Entity name must be a non-empty string: '{self.name}'")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got: {self.confidence}"
            )
        if self.type not in KNOWN_ENTITY_TYPES:
            raise ValueError(
                f"Unknown entity type '{self.type}'. Expected one of: {KNOWN_ENTITY_TYPES}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "confidence": round(float(self.confidence), 4),
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SemanticEntity:
        entity = cls(
            name=str(data.get("name", "")).strip(),
            type=str(data.get("type", "Entity")),
            confidence=float(data.get("confidence", 1.0)),
            attributes=dict(data.get("attributes", {})),
        )
        entity.validate()
        return entity


@dataclass
class SemanticStatement:
    """
    Represents an asserted fact, decision, claim, action, or outcome.
    """

    text: str
    type: str = "fact"
    confidence: float = 1.0
    target_entity: str | None = None

    def validate(self) -> None:
        if not self.text or not isinstance(self.text, str):
            raise ValueError(f"Statement text must be a non-empty string: '{self.text}'")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got: {self.confidence}"
            )
        if self.type not in KNOWN_STATEMENT_TYPES:
            raise ValueError(
                f"Unknown statement type '{self.type}'. Expected one of: {KNOWN_STATEMENT_TYPES}"
            )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "text": self.text,
            "type": self.type,
            "confidence": round(float(self.confidence), 4),
        }
        if self.target_entity is not None:
            result["target_entity"] = self.target_entity
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SemanticStatement:
        statement = cls(
            text=str(data.get("text", "")).strip(),
            type=str(data.get("type", "fact")),
            confidence=float(data.get("confidence", 1.0)),
            target_entity=data.get("target_entity"),
        )
        statement.validate()
        return statement


@dataclass
class SemanticExtractionRecord:
    """
    Complete semantic extraction output for a single message, retaining
    full bidirectional provenance to the source message, author, channel, and document.
    """

    document_id: str
    message_id: int
    message_index: int
    author: str
    channel: str
    message_text: str
    team: str | None = None
    source: str = "slack"
    entities: list[SemanticEntity] = field(default_factory=list)
    statements: list[SemanticStatement] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.document_id:
            raise ValueError("document_id must be a non-empty string.")
        if not isinstance(self.message_id, int) or self.message_id < 0:
            raise ValueError(
                f"message_id must be a non-negative integer, got: {self.message_id}"
            )
        if not isinstance(self.message_index, int) or self.message_index < 1:
            raise ValueError(
                f"message_index must be a positive integer >= 1, got: {self.message_index}"
            )
        for entity in self.entities:
            entity.validate()
        for statement in self.statements:
            statement.validate()

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "message_id": self.message_id,
            "message_index": self.message_index,
            "author": self.author,
            "team": self.team,
            "channel": self.channel,
            "source": self.source,
            "message_text": self.message_text,
            "entities": [e.to_dict() for e in self.entities],
            "statements": [s.to_dict() for s in self.statements],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SemanticExtractionRecord:
        record = cls(
            document_id=str(data["document_id"]),
            message_id=int(data["message_id"]),
            message_index=int(data["message_index"]),
            author=str(data.get("author", "unknown")),
            team=data.get("team"),
            channel=str(data.get("channel", "unknown")),
            source=str(data.get("source", "slack")),
            message_text=str(data.get("message_text", "")),
            entities=[
                SemanticEntity.from_dict(e) for e in data.get("entities", [])
            ],
            statements=[
                SemanticStatement.from_dict(s)
                for s in data.get("statements", [])
            ],
            metadata=dict(data.get("metadata", {})),
        )
        record.validate()
        return record
