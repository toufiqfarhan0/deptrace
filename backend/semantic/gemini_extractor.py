"""
Google Gemini Semantic Extraction for Slack Messages (Step 6E).

Uses the official Google GenAI SDK (google-genai) and Gemini
Interactions API with Pydantic structured JSON output.

The deterministic graph layer already handles:
- Person
- Team
- Channel
- Message
- Document

This module extracts higher-level semantic entities and statements.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from google import genai


# ---------------------------------------------------------------------------
# Project import setup
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass


try:
    from backend.semantic.schema import SemanticExtraction
except ImportError:
    from schema import SemanticExtraction  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Gemini extraction instructions
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are an enterprise knowledge graph extraction system.

Extract only semantic information from ONE Slack message that is:

1. explicitly supported by the message, AND
2. useful for future enterprise question answering.

Prefer precision over recall.

The deterministic graph layer already handles:
- Person
- Team
- Channel
- Message
- Document

Do NOT extract those as semantic entities.

============================================================
ALLOWED SEMANTIC ENTITY TYPES
============================================================

1. Customer

Use when the message explicitly names:
- a customer
- customer organization
- account
- tenant
- client organization

Examples:
- ACME
- AuroraHealth
- NotebookCo
- acct_233

Do NOT create a Customer merely because the generic word
"customer" appears.

------------------------------------------------------------

2. Project

Use for a named:
- project
- program
- initiative
- migration effort
- pilot
- workstream

Examples:
- Admit Splitter Migration
- Tenant Routing Pilot
- Customer Onboarding Revamp

Do NOT create a Project for generic phrases such as:
- migration plan
- rollout plan
- documentation plan
- checklist

unless the message clearly identifies the phrase as a named
project/program/initiative.

------------------------------------------------------------

3. Incident

Use for a concrete:
- outage
- service degradation
- production failure
- customer-impacting failure
- regression
- operational incident
- concrete troubleshooting event

Examples:
- ACME API latency incident
- streaming response truncation incident
- deploy regression
- production rollback incident

Do NOT create an Incident merely because the message contains:
- error
- failure
- latency
- timeout
- exception

The message must describe an actual operational/customer-impacting
event.

Do not classify a named artifact such as "DeployJob #445" as an Incident
unless the message explicitly identifies that artifact/event as the
incident itself.

------------------------------------------------------------

4. Decision

Use when the message explicitly records:
- a decision
- an approval
- a selected option
- an accepted direction
- a committed choice

Examples:
- approved option A
- decided to roll back v8.4.0
- agreed to use the canary rollout

Do NOT create a Decision merely from:
- a suggestion
- a proposal
- a question
- a possible future action

------------------------------------------------------------

5. ConfigurationChange

Use for a concrete change to:
- configuration
- policy
- routing
- threshold
- feature flag
- parameter
- model-selection setting
- access permission
- rollout setting
- operational setting

A ConfigurationChange should be extracted when the message describes
a setting/change as being:

- changed
- enabled
- disabled
- applied
- configured
- updated
- rolled out
- recommended as a concrete setting
- explicitly proposed as a concrete setting

Examples:
- tenant_concurrency_limit changed to 200
- enable fallback to lm-large
- strict_model:true
- soft-evict config
- access grant to group:oncall-readers
- route_if(...) rule
- a concrete feature flag value
- a routing policy change

IMPORTANT:

Do NOT create ConfigurationChange merely because a setting is mentioned.

For example:

"please check strict_model:true in the docs"

is NOT sufficient by itself.

But:

"enable strict_model:true for this rollout"

IS a ConfigurationChange.

------------------------------------------------------------

6. Entity

Use ONLY for a durable, named technical object that is useful for
cross-message retrieval or graph relationships and does not fit:

- Customer
- Project
- Incident
- Decision
- ConfigurationChange

Good examples:
- compact-model-v1
- primary-v2
- kernel-selector
- DeployJob #445
- INF-4921
- Grafana
- Redwood API
- billing-db
- a named service/component
- a named model
- a named infrastructure resource
- a named ticket

These are durable named technical objects or artifacts.

Do NOT use Entity for temporary activities, generic context, or
ordinary technical nouns.

Do NOT create Entity for:
- migration plan
- chaos tests
- checklist
- metrics dashboard
- synthetic requests
- documentation plan
- runbook
- ETA
- generic monitoring
- generic troubleshooting
- generic technical actions
- reproduction steps
- logs
- requests
- latency
- errors
- failures
- generic settings
- temporary activities

Prefer no entity over a low-value generic entity.

============================================================
STATEMENT TYPES
============================================================

Allowed statement types:

- fact
- decision
- claim
- action
- outcome

Use them as follows:

fact:
Information presented as established or observed.

decision:
An explicit accepted decision or committed choice.

claim:
An assertion, hypothesis, explanation, or uncertain statement.

action:
Work that someone proposes, plans, requests, or performs.

outcome:
A result observed after an action, change, or incident.

============================================================
EXTRACTION RULES
============================================================

1. Extract only information explicitly supported by the message.

2. Never invent:
   - entities
   - names
   - relationships
   - causes
   - outcomes
   - decisions

3. Prefer fewer high-value entities over many low-value entities.

4. A message may contain zero entities.

5. A message may contain zero statements.

6. Do not create an Entity merely because a noun is technical.

7. Preserve uncertainty:
   - confirmed/observed information -> fact
   - uncertain assertion/hypothesis -> claim

8. Use decision only for explicit decisions or accepted directions.

9. Use action for proposed, planned, requested, or executed work.

10. Use outcome for observed results.

11. ConfigurationChange must represent the concrete change itself,
    not merely the generic setting name.

12. Confidence must reflect both:
    - semantic correctness
    - evidence actually present in the message

13. Keep entity names concise and stable.

14. Do not extract Person names as semantic entities.

15. Do not extract Team, Channel, Message, or Document as semantic
    entities.

16. Do not output duplicate entities within the same message.

17. Do not rewrite the entire message into statements.

18. Extract only statements useful for future enterprise question
    answering.

19. If unsure whether something is a useful semantic entity, prefer
    returning no entity.

20. Preserve the distinction between:
    - proposal
    - decision
    - action
    - outcome

21. entity_refs in each statement must contain ONLY exact entity names
    extracted in the entities list of the SAME message.
    Never invent an entity reference or reference external entities.
    If a statement does not refer to any extracted entity, entity_refs
    MUST be [].

============================================================
ENTITY REFERENCES IN STATEMENTS (entity_refs)
============================================================

1. Entity extraction happens first conceptually.
2. Statements may reference zero or more extracted semantic entities.
3. entity_refs MUST match entity names extracted in the SAME message.
4. Do NOT invent an entity reference.
5. Do NOT reference Person, Team, Channel, Message, or Document.
6. Do NOT create entity_refs for entities that are not present in the
   message's semantic entity list.
7. If a statement is not about any extracted semantic entity, entity_refs
   must be [].

Example:

entities:
[
  {
    "type": "ConfigurationChange",
    "name": "strict_model:true",
    "confidence": 0.95
  }
]

statement:
{
  "text": "The unreleased strict_model:true flag is recommended in the docs draft.",
  "type": "action",
  "confidence": 0.95,
  "entity_refs": [
    "strict_model:true"
  ]
}

============================================================
OUTPUT EXPECTATIONS
============================================================

Return only the structured schema requested by the application.

Do not include:
- explanations
- markdown
- commentary
- extra fields
- provenance fields generated by the model

"""


class GeminiSemanticExtractor:
    """
    Semantic extractor using the Google GenAI SDK and Gemini
    Interactions API with structured Pydantic output.
    """

    def __init__(
        self,
        model: str = "gemini-3.5-flash",
    ) -> None:

        self.client = genai.Client()
        self.model = model

    def extract(
        self,
        message: dict[str, Any],
    ) -> SemanticExtraction:
        """
        Extract semantic entities/statements from one Slack message.

        Provenance is reattached by application code after the model
        response is validated.
        """

        message_id = int(
            message["message_id"]
        )

        document_id = str(
            message["document_id"]
        )

        prompt = f"""
Message provenance:

message_id: {message_id}
document_id: {document_id}
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
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        result = SemanticExtraction.model_validate_json(
            interaction.output_text
        )

        # -------------------------------------------------------------------
        # Provenance is controlled by our application, never by the model.
        # -------------------------------------------------------------------

        result.message_id = message_id
        result.document_id = document_id

        return result
