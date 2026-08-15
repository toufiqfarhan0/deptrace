from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest

from backend.semantic.sample_messages import (
    DEFAULT_OUTPUT_FILE,
    build_sample,
    classify_message,
    get_message_id,
    load_messages,
    stable_score,
)


def create_dummy_docs(num_docs: int = 20, msgs_per_doc: int = 10) -> list[dict]:
    docs = []
    for d in range(num_docs):
        doc_id = f"doc_{d:04d}__test_thread"
        msgs = []
        for m in range(msgs_per_doc):
            if m == 0:
                text = "Customer ACME reporting support issue with tenant latency."
            elif m == 1:
                text = "Incident confirmed: 502 error and p99 latency surge."
            elif m == 2:
                text = "Decision: rollback canary config ch_20260317_01 immediately."
            elif m == 3:
                text = "```\ncurl -X POST https://api.example.com/v1/retry\n```"
            elif m == 4:
                text = "ok"
            elif m == 5:
                text = "Detailed explanation " + ("words " * 150)
            elif m == 6:
                text = "@sam -> @raj cross-team dependency handoff."
            else:
                text = f"Standard discussion point number {m} regarding deployment."

            author = "deploy-bot" if m == 7 else f"user_{m}"
            team = "support" if m == 0 else f"team_{m}"
            msgs.append({"author": author, "team": team, "text": text})

        docs.append({"document_id": doc_id, "channel": "support", "messages": msgs})
    return docs


def test_stable_score_deterministic() -> None:
    score1 = stable_score(123456789)
    score2 = stable_score(123456789)
    score3 = stable_score(987654321)

    assert score1 == score2
    assert score1 != score3


def test_get_message_id_deterministic() -> None:
    id1 = get_message_id("doc-100", 3)
    id2 = get_message_id("doc-100", 3)
    id3 = get_message_id("doc-100", 4)

    assert id1 == id2
    assert id1 != id3
    assert id1 >= 0


def test_classify_message_categories() -> None:
    msg_cust = {"text": "Customer reported an issue to support team", "author": "sam", "team": "support"}
    cats_cust = classify_message(msg_cust)
    assert "customer_support" in cats_cust

    msg_inc = {"text": "502 error and latency spike degradation", "author": "alex", "team": "infra"}
    cats_inc = classify_message(msg_inc)
    assert "incident_technical" in cats_inc

    msg_code = {"text": "Run ```curl http://localhost:8080``` to test", "author": "jin", "team": "runtime"}
    cats_code = classify_message(msg_code)
    assert "code" in cats_code

    msg_bot = {"text": "Deployment finished", "author": "deploy-bot", "team": "infra"}
    cats_bot = classify_message(msg_bot)
    assert "bot" in cats_bot


def test_build_sample_invariants() -> None:
    docs = create_dummy_docs(num_docs=20, msgs_per_doc=10)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as tmp:
        tmp_path = Path(tmp.name)
        for doc in docs:
            tmp.write(json.dumps(doc) + "\n")

    try:
        messages = load_messages(tmp_path)
        assert len(messages) == 200

        sample_1 = build_sample(messages, target_size=100)
        sample_2 = build_sample(messages, target_size=100)

        # 1. Exactly 100 records
        assert len(sample_1) == 100

        # 2. Deterministic repeated output
        assert sample_1 == sample_2

        # 3. No duplicate message IDs
        msg_ids = [m["message_id"] for m in sample_1]
        assert len(msg_ids) == len(set(msg_ids))

        # 4. Message ID, document ID, and text preservation
        for item in sample_1:
            assert isinstance(item["message_id"], int)
            assert item["message_id"] >= 0
            assert isinstance(item["document_id"], str)
            assert item["document_id"].startswith("doc_")
            assert isinstance(item["message_index"], int)
            assert item["message_index"] >= 1
            assert isinstance(item["text"], str)
            assert len(item["text"]) > 0

        # 5. Sample spans multiple source documents
        unique_docs = {m["document_id"] for m in sample_1}
        assert len(unique_docs) > 10

    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def test_generated_sample_file_validation_if_exists() -> None:
    if not DEFAULT_OUTPUT_FILE.exists():
        pytest.skip(f"{DEFAULT_OUTPUT_FILE} does not exist on disk yet.")

    records = []
    with DEFAULT_OUTPUT_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    assert len(records) == 100, f"Expected 100 records, got {len(records)}"

    msg_ids = [r["message_id"] for r in records]
    assert len(msg_ids) == len(set(msg_ids)), "Duplicate message IDs found in sample_100.jsonl"

    for r in records:
        assert isinstance(r["message_id"], int) and r["message_id"] >= 0
        assert isinstance(r["document_id"], str) and len(r["document_id"]) > 0
        assert isinstance(r["message_index"], int) and r["message_index"] >= 1
        assert isinstance(r["text"], str) and len(r["text"]) > 0
        assert "channel" in r
        assert "author" in r

    unique_docs = {r["document_id"] for r in records}
    assert len(unique_docs) >= 50, f"Expected at least 50 unique documents, got {len(unique_docs)}"
