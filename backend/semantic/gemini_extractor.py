"""
Google Gemini Semantic Extraction for Slack Messages (Step 6C).

Utilizes the official Google GenAI SDK (google-genai) and Gemini Interactions API
with Pydantic structured JSON schemas to extract domain entities and statements.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from google import genai

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from backend.semantic.schema import SemanticExtraction
except ImportError:
    from schema import SemanticExtraction  # type: ignore[no-redef]


SYSTEM_INSTRUCTIONS = """
You are an enterprise knowledge extraction system.

Extract semantic enterprise knowledge from ONE Slack message.

Extract ONLY information explicitly supported by the message.

Semantic entity types:
- Customer
- Project
- Incident
- Decision
- ConfigurationChange
- Entity

Do NOT extract:
- Person
- Team
- Channel
- Message
- Document

These are handled by the deterministic graph layer.

Statement types:
- fact
- decision
- claim
- action
- outcome

Rules:
1. Never invent an entity.
2. Never invent a statement.
3. Do not infer unsupported relationships.
4. Keep entity names concise.
5. Use Entity for technical concepts that do not fit another type.
6. Extract meaningful statements instead of rewriting every sentence.
7. Confidence must be between 0 and 1.
8. Return empty arrays when the message contains no useful semantic information.
9. Preserve the distinction between claims and confirmed facts.
10. Do not extract people as semantic entities.
""".strip()


class GeminiSemanticExtractor:
    """
    Semantic extractor utilizing Google GenAI Interactions API with structured JSON output.
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
    ) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            # genai.Client() also checks GEMINI_API_KEY environment variable automatically
            pass

        self.client = genai.Client()
        self.model = model

    def extract(
        self,
        message: dict[str, Any],
    ) -> SemanticExtraction:
        """
        Extract structured entities and statements from a single message,
        enforcing deterministic provenance reattachment in application code.
        """
        prompt = f"""
Message provenance:

message_id: {message["message_id"]}
document_id: {message["document_id"]}
author: {message.get("author")}
team: {message.get("team")}
channel: {message.get("channel")}

Message:

{message["text"]}
""".strip()

        interaction = self.client.interactions.create(
            model=self.model,
            input=prompt,
            system_instruction=SYSTEM_INSTRUCTIONS,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": SemanticExtraction.model_json_schema(),
            },
        )

        if not interaction.output_text:
            raise RuntimeError("Gemini returned an empty response.")

        result = SemanticExtraction.model_validate_json(interaction.output_text)

        # Re-attach deterministic source provenance in application code
        result.message_id = int(message["message_id"])
        result.document_id = str(message["document_id"])

        return result