"""
Gemini Answer Generator for Graph RAG (Step 8).

Formats deterministic evidence bundles with explicit stable identifiers [E1, E2, ...]
and calls Gemini via the google-genai SDK under strict grounding instructions.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass

try:
    from backend.retrieval.models import EvidenceItem

except ImportError:
    from models import EvidenceItem  # type: ignore[no-redef]

RAG_SYSTEM_INSTRUCTIONS = """You are an enterprise knowledge assistant answering questions based strictly on the provided evidence bundle retrieved from the company graph.

CRITICAL GROUNDING RULES:
1. Answer ONLY using the facts, entities, and statements present in the supplied evidence bundle.
2. Every substantive claim or fact in your answer MUST cite its supporting evidence item using bracket notation like [E1], [E2], etc.
3. If the supplied evidence bundle is empty or does not contain enough information to answer the question, clearly state: "The available evidence is insufficient to answer this question."
4. Do NOT invent, assume, or extrapolate facts, timestamps, people, tickets, metrics, or relationships not explicitly present in the evidence.
5. Do NOT invent citation identifiers (e.g. do not cite [E99] if only [E1] through [E3] exist).
6. Distinguish clearly between facts, decisions, actions, claims, and outcomes as recorded in the evidence.
7. Keep your answer concise, direct, and enterprise-oriented.
"""


def format_evidence_bundle(labeled_evidence: list[tuple[str, EvidenceItem]]) -> str:
    """Format labeled evidence items into a structured prompt section."""
    if not labeled_evidence:
        return "No evidence retrieved."

    lines: list[str] = []
    for label, item in labeled_evidence:
        lines.append(f"[{label}]")
        lines.append(f"  - Message ID:  {item.message_id}")
        lines.append(f"  - Document ID: {item.document_id}")
        if item.entity_name:
            lines.append(f"  - Entity:      {item.entity_name}")
        if item.statement:
            stype = f"[{item.statement_type}] " if item.statement_type else ""
            lines.append(f"  - Statement:   {stype}{item.statement}")
        if item.relationship:
            lines.append(f"  - Graph Rel:   {item.relationship}")
        lines.append("")

    return "\n".join(lines).strip()


class GeminiAnswerGenerator:
    """
    Answer generator using Google GenAI SDK and Gemini Interactions API.
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
    ) -> None:
        self.client = genai.Client()
        self.model = model

    def generate_answer(
        self,
        question: str,
        labeled_evidence: list[tuple[str, EvidenceItem]],
    ) -> str:
        """
        Generate a grounded answer for the user question given the labeled evidence bundle.
        """
        formatted_evidence = format_evidence_bundle(labeled_evidence)

        user_content = f"""QUESTION:
{question}

RETRIEVED EVIDENCE BUNDLE:
{formatted_evidence}

Please provide a concise, grounded answer citing the relevant evidence items ([E1], [E2], etc.)."""

        config = types.GenerateContentConfig(
            system_instruction=RAG_SYSTEM_INSTRUCTIONS,
            temperature=0.0,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_content,
            config=config,
        )

        if not response or not response.text:
            return "Unable to generate answer from model."

        return response.text.strip()
