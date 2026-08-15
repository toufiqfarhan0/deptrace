"""
Unit tests for HydraDB candidate ingestion and query builder.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from backend.graph.ingest_candidates import (
    build_merge_query,
    enrich_relationship,
    escape_string_property,
    load_documents,
    node_fragment,
    validate_identifier,
)


class TestIngestCandidates(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_candidate = {
            "document_id": "dsid_test_001__12345-incident",
            "source": "slack",
            "channel": "support",
            "nodes": [
                {
                    "label": "Document",
                    "id": 1001,
                    "document_id": "dsid_test_001__12345-incident",
                    "source": "slack",
                },
                {
                    "label": "Channel",
                    "id": 2001,
                    "name": "support",
                },
                {
                    "label": "Message",
                    "id": 3001,
                    "document_id": "dsid_test_001__12345-incident",
                    "message_index": 1,
                    "author": "alex",
                    "team": "support",
                    "channel": "support",
                    "text": "Latency is high' across instances\ncheck immediately",
                },
                {
                    "label": "Person",
                    "id": 4001,
                    "name": "alex",
                },
                {
                    "label": "Team",
                    "id": 5001,
                    "name": "support",
                },
            ],
            "relationships": [
                {
                    "type": "IN_CHANNEL",
                    "id": 9001,
                    "from": {"label": "Document", "id": 1001},
                    "to": {"label": "Channel", "id": 2001},
                },
                {
                    "type": "AUTHORED",
                    "id": 9002,
                    "from": {"label": "Person", "id": 4001},
                    "to": {"label": "Message", "id": 3001},
                },
                {
                    "type": "MEMBER_OF",
                    "id": 9003,
                    "from": {"label": "Person", "id": 4001},
                    "to": {"label": "Team", "id": 5001},
                },
                {
                    "type": "IN_CHANNEL",
                    "id": 9004,
                    "from": {"label": "Message", "id": 3001},
                    "to": {"label": "Channel", "id": 2001},
                },
                {
                    "type": "PART_OF",
                    "id": 9005,
                    "from": {"label": "Message", "id": 3001},
                    "to": {"label": "Document", "id": 1001},
                },
            ],
        }

    def test_build_merge_query_syntax(self) -> None:
        rel = self.sample_candidate["relationships"][1]  # Person -> Message
        enriched = enrich_relationship(self.sample_candidate, rel)
        query = build_merge_query(enriched)

        self.assertTrue(query.startswith("MERGE "))
        self.assertIn("(person:Person {id: 4001, name: 'alex'})", query)
        self.assertIn("-[:AUTHORED {id: 9002}]->", query)
        self.assertIn("(message:Message {", query)
        self.assertIn("author: 'alex'", query)
        self.assertIn("message_index: 1", query)

    def test_integer_ids_enforced_in_query(self) -> None:
        rel = self.sample_candidate["relationships"][0]  # Document -> Channel
        enriched = enrich_relationship(self.sample_candidate, rel)
        query = build_merge_query(enriched)

        # Confirm integer IDs are rendered as bare integers, not strings
        self.assertIn("id: 1001", query)
        self.assertIn("id: 2001", query)
        self.assertIn("id: 9001", query)
        self.assertNotIn("id: '1001'", query)
        self.assertNotIn("id: '9001'", query)

    def test_endpoint_property_mapping(self) -> None:
        rel = self.sample_candidate["relationships"][3]  # Message -> Channel
        enriched = enrich_relationship(self.sample_candidate, rel)

        self.assertEqual(enriched["from"]["label"], "Message")
        self.assertEqual(enriched["from"]["id"], 3001)
        self.assertEqual(
            enriched["from"]["properties"]["document_id"],
            "dsid_test_001__12345-incident",
        )
        self.assertEqual(enriched["from"]["properties"]["author"], "alex")
        self.assertEqual(enriched["from"]["properties"]["message_index"], 1)

        self.assertEqual(enriched["to"]["label"], "Channel")
        self.assertEqual(enriched["to"]["id"], 2001)
        self.assertEqual(enriched["to"]["properties"]["name"], "support")

    def test_string_escaping_and_unsupported_property_handling(self) -> None:
        # Test string property escaping
        raw_text = "it's a test \\ with 'quotes' and \n newline"
        escaped = escape_string_property(raw_text)
        self.assertEqual(escaped, "its a test  with quotes and   newline")

        # Test node_fragment with string property
        fragment = node_fragment("Person", 100, {"name": "O'Connor"})
        self.assertEqual(fragment, "(person:Person {id: 100, name: 'OConnor'})")

        # Test unsupported property type raises ValueError
        with self.assertRaises(ValueError):
            node_fragment("Person", 100, {"nested": {"key": "val"}})

        # Test unsafe identifier raises ValueError
        with self.assertRaises(ValueError):
            validate_identifier("Person; DROP TABLE--")

    def test_document_limit_behavior(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".jsonl",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp_path = Path(tmp.name)
            for i in range(15):
                tmp.write(
                    json.dumps({"document_id": f"doc_{i}", "nodes": [], "relationships": []})
                    + "\n"
                )

        try:
            docs_all = load_documents(tmp_path, limit=0)
            self.assertEqual(len(docs_all), 15)

            docs_limit_5 = load_documents(tmp_path, limit=5)
            self.assertEqual(len(docs_limit_5), 5)
            self.assertEqual(docs_limit_5[0]["document_id"], "doc_0")
            self.assertEqual(docs_limit_5[4]["document_id"], "doc_4")

            docs_limit_10 = load_documents(tmp_path, limit=10)
            self.assertEqual(len(docs_limit_10), 10)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
