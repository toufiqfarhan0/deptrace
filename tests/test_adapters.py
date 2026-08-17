"""
Offline unit tests for Canonical Multi-Source Ingestion & Adapters (Step 13B).

Validates:
1. SlackAdapter, LinearAdapter, GitHubAdapter parsing
2. CanonicalRecord normalization & metadata preservation
3. Deterministic ID generation (same key -> same ID, diff source -> diff ID)
4. Cross-source reference extraction (Issue keys, PR numbers, user mentions)
5. Ambiguous identity resolution
6. HydraEnterpriseWriter single-hop MERGE query formatting
7. 100% offline with zero Gemini API calls
"""

from __future__ import annotations

import pytest

from backend.ingestion.adapters import (
    GitHubAdapter,
    LinearAdapter,
    SlackAdapter,
    get_adapter_for_source,
)
from backend.ingestion.canonical import CanonicalRecord
from backend.ingestion.references import (
    extract_explicit_references,
    resolve_person_identity,
)
from backend.ingestion.writer import HydraEnterpriseWriter
from backend.semantic.ids import stable_id


# --- FIXTURE DATA ---

SLACK_FIXTURE = """incidents

alex (support): Heads-up ACME reporting p99 API latency 3x since 18:30 UTC. See INC-2026 and REL-311.
sam (eng-runtime): looking. Related to PR #99501. Can @omar check gateway logs?
[2026-03-15T10:02:11Z] gateway: writev broken pipe
"""

LINEAR_FIXTURE = """Commitment gap auditor and rollback impact simulator

Goal: Add runtime auditor that detects divergence between committed throughput and observed delivery.
Scope: Design auditor service for Dedicated tier.
Checklist:
- [x] design doc
- [x] unit & integration tests
Related: SUP-4312, ENG-1982, PR-947999

2026-02-21 - Aisha Patel: Kicked off design doc.
2026-02-26 - Architecture sync (Marco Alvarez, Lena Cho): agreed on deterministic scoring.
"""

GITHUB_FIXTURE = """Add service-scoped KMS guardrails and audit ingestion harmonizer

Motivation: Customers operating multiple services require strict key isolation. Fixes ENG-4821 and relates to INC-2026.

Summary of changes:
- Adds new enforcement middleware kms/service-guard.
- Introduces policy API.

Arjun: Nice incremental approach. Please add a unit test simulating preemption.
Maya: Added test and documented KV cache assumption.
"""


def test_slack_adapter_parsing() -> None:
    adapter = SlackAdapter()
    rec = adapter.parse_content(
        filename="dsid_00193d850bed4293aa8250edf1fbe2da__3287654321-waitlisting-fairness.txt",
        content=SLACK_FIXTURE,
    )

    assert isinstance(rec, CanonicalRecord)
    assert rec.source == "slack"
    assert rec.source_id == "3287654321"
    assert rec.document_id == "dsid_00193d850bed4293aa8250edf1fbe2da"
    assert rec.record_type == "conversation"
    assert rec.channel == "incidents"
    assert rec.author == "alex"
    assert "sam" in rec.participants
    assert rec.timestamp == "2026-03-15T10:02:11Z"
    assert "INC-2026" in rec.external_refs
    assert "REL-311" in rec.external_refs
    assert "PR-99501" in rec.external_refs


def test_linear_adapter_parsing() -> None:
    adapter = LinearAdapter()
    rec = adapter.parse_content(
        filename="dsid_000109e255fd4d4090f68a0b3be6e1a3__ENG-30521-interop-fallback.txt",
        content=LINEAR_FIXTURE,
    )

    assert isinstance(rec, CanonicalRecord)
    assert rec.source == "linear"
    assert rec.source_id == "ENG-30521"
    assert rec.document_id == "dsid_000109e255fd4d4090f68a0b3be6e1a3"
    assert rec.record_type == "issue"
    assert rec.project == "ENG"
    assert rec.author == "Aisha Patel"
    assert "Aisha Patel" in rec.participants
    assert "Marco Alvarez" in rec.participants
    assert rec.timestamp == "2026-02-21"
    assert "SUP-4312" in rec.external_refs
    assert "ENG-1982" in rec.external_refs


def test_github_adapter_parsing() -> None:
    adapter = GitHubAdapter()
    rec = adapter.parse_content(
        filename="dsid_000bf89dcd294f369b4a91efe64c2aca__pr-99501-add-service-scoped-kms.txt",
        content=GITHUB_FIXTURE,
    )

    assert isinstance(rec, CanonicalRecord)
    assert rec.source == "github"
    assert rec.source_id == "PR-99501"
    assert rec.document_id == "dsid_000bf89dcd294f369b4a91efe64c2aca"
    assert rec.record_type == "pull_request"
    assert rec.author == "Arjun"
    assert "Arjun" in rec.participants
    assert "Maya" in rec.participants
    assert "ENG-4821" in rec.external_refs
    assert "INC-2026" in rec.external_refs


def test_adapter_factory() -> None:
    assert isinstance(get_adapter_for_source("slack"), SlackAdapter)
    assert isinstance(get_adapter_for_source("linear"), LinearAdapter)
    assert isinstance(get_adapter_for_source("github"), GitHubAdapter)

    with pytest.raises(ValueError, match="Unsupported enterprise source"):
        get_adapter_for_source("jira")


def test_deterministic_stable_ids() -> None:
    doc_id = "dsid_00193d850bed4293aa8250edf1fbe2da"

    # Same source + same doc_id -> same ID
    id_slack_1 = stable_id("slack", doc_id)
    id_slack_2 = stable_id("slack", doc_id)
    assert id_slack_1 == id_slack_2
    assert id_slack_1 > 0
    assert id_slack_1 <= 0x7FFFFFFFFFFFFFFF

    # Different source + same doc_id -> different ID
    id_linear = stable_id("linear", doc_id)
    id_github = stable_id("github", doc_id)
    assert id_slack_1 != id_linear
    assert id_slack_1 != id_github
    assert id_linear != id_github


def test_reference_extraction() -> None:
    text = "Follow up on INC-2026 and ENG-4821. PR #99501 merged by @omar and @aisha_patel."
    refs = extract_explicit_references(text)

    ref_map = {(r.ref_type, r.ref_value) for r in refs}
    assert ("issue", "INC-2026") in ref_map
    assert ("issue", "ENG-4821") in ref_map
    assert ("pr", "PR-99501") in ref_map
    assert ("user", "omar") in ref_map
    assert ("user", "aisha_patel") in ref_map


def test_person_identity_resolution() -> None:
    # Full name -> resolved with high confidence
    res_full = resolve_person_identity("Aisha Patel", source="linear")
    assert res_full.is_ambiguous is False
    assert res_full.confidence >= 0.90
    assert res_full.canonical_name == "Aisha Patel"

    # Handle with role qualifier -> resolved
    res_role = resolve_person_identity("sam", source="slack", role_or_context="eng-runtime")
    assert res_role.is_ambiguous is False
    assert res_role.confidence >= 0.80
    assert "eng-runtime" in res_role.canonical_name

    # Ambiguous common single name without qualification -> marked ambiguous
    res_ambig = resolve_person_identity("alex", source="slack")
    assert res_ambig.is_ambiguous is True
    assert res_ambig.confidence < 0.50


def test_writer_merge_statements_generation() -> None:
    adapter = SlackAdapter()
    rec = adapter.parse_content(
        filename="dsid_00193d850bed4293aa8250edf1fbe2da__3287654321-waitlisting.txt",
        content=SLACK_FIXTURE,
    )

    writer = HydraEnterpriseWriter()
    stmts = writer.generate_merge_statements(rec)

    assert len(stmts) >= 3  # In_Channel + Authored + Mentions

    # Check that statements strictly follow single-hop MERGE syntax:
    # MERGE (a:Label {...})-[:REL {...}]->(b:Label {...})
    for s in stmts:
        assert s.startswith("MERGE (")
        assert "-[:" in s
        assert "]->(" in s
        assert "document_id: 'dsid_00193d850bed4293aa8250edf1fbe2da'" in s


def test_malformed_documents() -> None:
    adapter = SlackAdapter()
    # Empty content
    rec_empty = adapter.parse_content("dsid_empty__0000.txt", "")
    assert rec_empty.source == "slack"
    assert rec_empty.document_id == "dsid_empty"
    assert len(rec_empty.participants) == 0

    # Content with no message headers
    rec_raw = adapter.parse_content("dsid_raw__1111.txt", "just some raw text with no headers")
    assert rec_raw.channel == "just some raw text with no headers"
    assert rec_raw.author is None
