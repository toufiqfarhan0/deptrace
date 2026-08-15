"""
Base Extractor Interfaces and Heuristic Baseline Extractor.

Defines the pluggable extraction contract that model providers (Gemini, OpenAI,
Anthropic, Local) or baseline heuristic extractors implement.
"""

from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.extraction.schema import (
    SemanticEntity,
    SemanticExtractionRecord,
    SemanticStatement,
)
from backend.ingestion.build_graph_candidates import stable_id


# Domain patterns for heuristic baseline extraction
RE_CONFIG_CHANGE = re.compile(r"\b(ch_\d{8}_\d{2}|v\d+\.\d+\.\d+(?:-[\w]+)?)\b", re.IGNORECASE)
RE_CUSTOMER = re.compile(
    r"\b(ACME|AuroraHealth|BlueCrest|DataSigma|LumosCare|StratusHealth|Tidewell|OroTech|BloomPay|CredoHealth)\b",
    re.IGNORECASE,
)
RE_INCIDENT = re.compile(
    r"\b(latency spike|p99 API latency|broken pipe|connection drop|502 error|throttle rejection|degradation|outage|incident)\b",
    re.IGNORECASE,
)
RE_DECISION = re.compile(
    r"\b(mitigation:|root cause:|action plan:|decision:|recommending follow-up:|action items?:)\s*(.+?)(?:\.|$)",
    re.IGNORECASE,
)


class BaseExtractor(ABC):
    """
    Abstract Base Class for semantic extractors.
    """

    @abstractmethod
    def extract_message(
        self,
        message: dict[str, Any],
        document_context: dict[str, Any] | None = None,
    ) -> SemanticExtractionRecord:
        """
        Extract semantic entities and statements from a single Slack message.
        """
        pass

    def extract_batch(
        self,
        messages: list[dict[str, Any]],
        document_context: dict[str, Any] | None = None,
    ) -> list[SemanticExtractionRecord]:
        """
        Extract semantic entities and statements from a batch of messages.
        """
        return [
            self.extract_message(msg, document_context=document_context)
            for msg in messages
        ]


class HeuristicExtractor(BaseExtractor):
    """
    Deterministic rule-based extractor using regular expressions and keywords.
    Provides an offline baseline and test harness without external API dependencies.
    """

    def __init__(self, name: str = "heuristic-baseline-v1") -> None:
        self.name = name

    def extract_message(
        self,
        message: dict[str, Any],
        document_context: dict[str, Any] | None = None,
    ) -> SemanticExtractionRecord:
        doc_ctx = document_context or {}
        document_id = str(message.get("document_id") or doc_ctx.get("document_id") or "unknown")
        channel = str(message.get("channel") or doc_ctx.get("channel") or "unknown")
        author = str(message.get("author") or "unknown")
        team = message.get("team") or doc_ctx.get("team")
        message_index = int(message.get("message_index", 1))
        text = str(message.get("text", "")).strip()

        message_id = message.get("id")
        if message_id is None:
            message_id = stable_id("message", f"{document_id}:{message_index}")
        else:
            message_id = int(message_id)

        entities: list[SemanticEntity] = []
        statements: list[SemanticStatement] = []

        # 1. Customer detection
        for match in RE_CUSTOMER.finditer(text):
            cust_name = match.group(1).upper() if match.group(1).lower() == "acme" else match.group(1)
            entities.append(
                SemanticEntity(
                    name=cust_name,
                    type="Customer",
                    confidence=0.95,
                )
            )

        # 2. Configuration change detection
        for match in RE_CONFIG_CHANGE.finditer(text):
            change_id = match.group(1)
            entities.append(
                SemanticEntity(
                    name=change_id,
                    type="ConfigurationChange",
                    confidence=0.90,
                    attributes={"change_key": change_id},
                )
            )

        # 3. Incident detection
        for match in RE_INCIDENT.finditer(text):
            inc_phrase = match.group(1).strip()
            entities.append(
                SemanticEntity(
                    name=inc_phrase,
                    type="Incident",
                    confidence=0.85,
                )
            )

        # 4. Decisions and action statements
        for match in RE_DECISION.finditer(text):
            statement_type = "decision" if "decision" in match.group(1).lower() else "action"
            stmt_text = match.group(0).strip()
            statements.append(
                SemanticStatement(
                    text=stmt_text,
                    type=statement_type,
                    confidence=0.85,
                )
            )

        # If no specific statement was captured, add a fact statement if text is substantial
        if not statements and len(text) > 20:
            statements.append(
                SemanticStatement(
                    text=text[:150] + ("..." if len(text) > 150 else ""),
                    type="fact",
                    confidence=0.75,
                )
            )

        # Deduplicate entities by (type, name)
        unique_entities: list[SemanticEntity] = []
        seen_entity_keys: set[tuple[str, str]] = set()
        for entity in entities:
            key = (entity.type, entity.name.lower())
            if key not in seen_entity_keys:
                seen_entity_keys.add(key)
                unique_entities.append(entity)

        return SemanticExtractionRecord(
            document_id=document_id,
            message_id=message_id,
            message_index=message_index,
            author=author,
            team=team,
            channel=channel,
            source="slack",
            message_text=text,
            entities=unique_entities,
            statements=statements,
            metadata={"extractor": self.name},
        )
