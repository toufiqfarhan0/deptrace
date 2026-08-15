"""
Unit tests for Step 6 Semantic Extraction Foundation.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from backend.extraction.base import HeuristicExtractor
from backend.extraction.schema import (
    KNOWN_ENTITY_TYPES,
    KNOWN_STATEMENT_TYPES,
    SemanticEntity,
    SemanticExtractionRecord,
    SemanticStatement,
)
from backend.extraction.selector import (
    select_messages_by_keywords,
    select_messages_sample,
)


class TestSemanticExtraction(unittest.TestCase):
    def test_entity_schema_valid_and_invalid(self) -> None:
        # Valid entity
        entity = SemanticEntity(
            name="ACME",
            type="Customer",
            confidence=0.95,
            attributes={"tier": "enterprise"},
        )
        entity.validate()
        data = entity.to_dict()
        self.assertEqual(data["name"], "ACME")
        self.assertEqual(data["type"], "Customer")
        self.assertEqual(data["confidence"], 0.95)
        self.assertEqual(data["attributes"]["tier"], "enterprise")

        # Roundtrip
        reconstituted = SemanticEntity.from_dict(data)
        self.assertEqual(reconstituted.name, entity.name)
        self.assertEqual(reconstituted.type, entity.type)

        # Invalid: empty name
        with self.assertRaises(ValueError):
            SemanticEntity(name="", type="Customer").validate()

        # Invalid: confidence out of bounds
        with self.assertRaises(ValueError):
            SemanticEntity(name="ACME", type="Customer", confidence=1.5).validate()
        with self.assertRaises(ValueError):
            SemanticEntity(name="ACME", type="Customer", confidence=-0.1).validate()

        # Invalid: unknown type
        with self.assertRaises(ValueError):
            SemanticEntity(name="ACME", type="InvalidType").validate()

    def test_statement_schema_valid_and_invalid(self) -> None:
        # Valid statement
        stmt = SemanticStatement(
            text="Increased ACME concurrency to 200 to mitigate queue stall.",
            type="action",
            confidence=0.9,
            target_entity="ACME",
        )
        stmt.validate()
        data = stmt.to_dict()
        self.assertEqual(data["type"], "action")
        self.assertEqual(data["target_entity"], "ACME")

        # Roundtrip
        reconstituted = SemanticStatement.from_dict(data)
        self.assertEqual(reconstituted.text, stmt.text)
        self.assertEqual(reconstituted.type, stmt.type)
        self.assertEqual(reconstituted.target_entity, stmt.target_entity)

        # Invalid: empty text
        with self.assertRaises(ValueError):
            SemanticStatement(text="", type="fact").validate()

        # Invalid: unknown statement type
        with self.assertRaises(ValueError):
            SemanticStatement(text="Something", type="opinion").validate()

    def test_record_validation_and_provenance(self) -> None:
        record = SemanticExtractionRecord(
            document_id="dsid_001__incident",
            message_id=40001,
            message_index=1,
            author="sam",
            team="eng-runtime",
            channel="support",
            source="slack",
            message_text="Applying configuration change ch_20260317_01 for ACME.",
            entities=[
                SemanticEntity(name="ACME", type="Customer"),
                SemanticEntity(name="ch_20260317_01", type="ConfigurationChange"),
            ],
            statements=[
                SemanticStatement(text="Applying configuration change", type="action")
            ],
            metadata={"model": "test-v1"},
        )
        record.validate()
        data = record.to_dict()

        # Check provenance fields
        self.assertEqual(data["document_id"], "dsid_001__incident")
        self.assertEqual(data["message_id"], 40001)
        self.assertEqual(data["message_index"], 1)
        self.assertEqual(data["author"], "sam")
        self.assertEqual(data["team"], "eng-runtime")
        self.assertEqual(data["channel"], "support")
        self.assertEqual(data["source"], "slack")
        self.assertEqual(len(data["entities"]), 2)
        self.assertEqual(len(data["statements"]), 1)

        # Roundtrip
        reconstituted = SemanticExtractionRecord.from_dict(data)
        self.assertEqual(reconstituted.document_id, record.document_id)
        self.assertEqual(reconstituted.message_id, record.message_id)
        self.assertEqual(len(reconstituted.entities), 2)

        # Invalid message_id
        with self.assertRaises(ValueError):
            SemanticExtractionRecord(
                document_id="dsid_001",
                message_id=-1,
                message_index=1,
                author="sam",
                channel="support",
                message_text="hi",
            ).validate()

        # Invalid message_index
        with self.assertRaises(ValueError):
            SemanticExtractionRecord(
                document_id="dsid_001",
                message_id=1,
                message_index=0,
                author="sam",
                channel="support",
                message_text="hi",
            ).validate()

    def test_empty_extraction(self) -> None:
        record = SemanticExtractionRecord(
            document_id="dsid_002__empty",
            message_id=102,
            message_index=2,
            author="alex",
            channel="random",
            message_text="Good morning team!",
            entities=[],
            statements=[],
        )
        record.validate()
        data = record.to_dict()
        self.assertEqual(data["entities"], [])
        self.assertEqual(data["statements"], [])

    def test_multiple_entities_and_statements(self) -> None:
        entities = [
            SemanticEntity(name="ACME", type="Customer"),
            SemanticEntity(name="Redwood", type="Project"),
            SemanticEntity(name="Latency Surge", type="Incident"),
            SemanticEntity(name="ch_20260317_01", type="ConfigurationChange"),
        ]
        statements = [
            SemanticStatement(text="Queue spiked to 410 requests", type="fact"),
            SemanticStatement(text="Decision: bump concurrency cap", type="decision"),
            SemanticStatement(text="Redwoodctl executed successfully", type="outcome"),
        ]
        record = SemanticExtractionRecord(
            document_id="dsid_003__multi",
            message_id=301,
            message_index=3,
            author="elaine",
            channel="support",
            message_text="Multi entity test message.",
            entities=entities,
            statements=statements,
        )
        record.validate()
        self.assertEqual(len(record.entities), 4)
        self.assertEqual(len(record.statements), 3)

    def test_heuristic_extractor_provenance_and_extraction(self) -> None:
        extractor = HeuristicExtractor()
        sample_msg = {
            "document_id": "dsid_00193d850bed4293aa8250edf1fbe2da__3287654321-waitlisting-fairness",
            "channel": "support",
            "message_index": 8,
            "author": "sam",
            "team": "eng-runtime",
            "text": "Quick mitigation: temporarily bump ACME concurrency to 200. Change id: ch_20260317_01. Decision: auto-fallback policy.",
        }

        record = extractor.extract_message(sample_msg)
        record.validate()

        # Check provenance
        self.assertEqual(record.document_id, sample_msg["document_id"])
        self.assertEqual(record.author, "sam")
        self.assertEqual(record.team, "eng-runtime")
        self.assertEqual(record.channel, "support")
        self.assertEqual(record.message_index, 8)
        self.assertGreaterEqual(record.message_id, 0)

        # Check extracted entities
        entity_types = {e.type for e in record.entities}
        self.assertIn("Customer", entity_types)
        self.assertIn("ConfigurationChange", entity_types)

        cust_entity = next(e for e in record.entities if e.type == "Customer")
        self.assertEqual(cust_entity.name, "ACME")

        config_entity = next(e for e in record.entities if e.type == "ConfigurationChange")
        self.assertEqual(config_entity.name, "ch_20260317_01")

        # Check statement
        stmt_types = {s.type for s in record.statements}
        self.assertIn("decision", stmt_types)

    def test_selector_message_provenance(self) -> None:
        sample_docs = [
            {
                "document_id": "doc_1",
                "channel": "support",
                "messages": [
                    {"author": "alex", "team": "support", "text": "ACME outage incident."},
                    {"author": "sam", "team": "runtime", "text": "Investigating."},
                ],
            },
            {
                "document_id": "doc_2",
                "channel": "infra",
                "messages": [
                    {"author": "raj", "team": "sre", "text": "Rolled canary config ch_20260318_01."},
                ],
            },
        ]

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".jsonl",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp_path = Path(tmp.name)
            for doc in sample_docs:
                tmp.write(json.dumps(doc) + "\n")

        try:
            sample_slice = select_messages_sample(tmp_path, limit_documents=2, max_messages_per_doc=2)
            self.assertEqual(len(sample_slice), 3)

            for item in sample_slice:
                self.assertIn("id", item)
                self.assertIsInstance(item["id"], int)
                self.assertGreaterEqual(item["id"], 0)
                self.assertIn("document_id", item)
                self.assertIn("channel", item)
                self.assertIn("message_index", item)
                self.assertIn("author", item)
                self.assertIn("text", item)

            # Keyword filtering
            kw_slice = select_messages_by_keywords(["canary"], input_file=tmp_path)
            self.assertEqual(len(kw_slice), 1)
            self.assertEqual(kw_slice[0]["document_id"], "doc_2")
            self.assertEqual(kw_slice[0]["author"], "raj")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
