"""
Unit tests for deterministic Slack graph candidate generator.
"""

from __future__ import annotations

import json
import unittest
from backend.ingestion.build_graph_candidates import (
    build_candidate_document,
    stable_id,
)


class TestBuildGraphCandidates(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_document = {
            "document_id": "dsid_00193d850bed4293aa8250edf1fbe2da__3287654321-waitlisting-fairness",
            "source": "slack",
            "channel": "support",
            "messages": [
                {
                    "author": "alex",
                    "team": "support",
                    "text": "Heads-up — ACME reporting p99 API latency ~3x since ~18:30 UTC yesterday.",
                },
                {
                    "author": "sam",
                    "team": "eng-runtime",
                    "text": "looking. Can you paste a sample request id / trace?",
                },
                {
                    "author": "elaine",
                    "team": "eng-sre",
                    "text": "Metrics show request_queue_length for region us-west-2 jumped from 40 -> 410.",
                },
            ],
            "message_count": 3,
        }

    def test_deterministic_ids_are_non_negative_integers(self) -> None:
        id1 = stable_id("person", "alex")
        id2 = stable_id("channel", "support")
        id3 = stable_id("message", "dsid_001:1")

        self.assertIsInstance(id1, int)
        self.assertIsInstance(id2, int)
        self.assertIsInstance(id3, int)

        self.assertGreaterEqual(id1, 0)
        self.assertGreaterEqual(id2, 0)
        self.assertGreaterEqual(id3, 0)

        # Ensure fits within 63-bit signed integer space
        self.assertLess(id1, 2**63)
        self.assertLess(id2, 2**63)
        self.assertLess(id3, 2**63)

    def test_stable_id_is_deterministic_and_namespaced(self) -> None:
        id_a1 = stable_id("person", "alex")
        id_a2 = stable_id("person", "alex")
        id_team = stable_id("team", "alex")

        # Same namespace and value must return exact same ID
        self.assertEqual(id_a1, id_a2)

        # Different namespace with same value must produce different ID
        self.assertNotEqual(id_a1, id_team)

    def test_parse_one_candidate_document(self) -> None:
        candidate = build_candidate_document(self.sample_document)

        self.assertEqual(
            candidate["document_id"],
            "dsid_00193d850bed4293aa8250edf1fbe2da__3287654321-waitlisting-fairness",
        )
        self.assertEqual(candidate["source"], "slack")
        self.assertEqual(candidate["channel"], "support")
        self.assertIn("nodes", candidate)
        self.assertIn("relationships", candidate)

        # 1 Document + 1 Channel + (3 * 3 Message/Person/Team) = 11 nodes
        self.assertEqual(len(candidate["nodes"]), 11)

        # 1 Doc->Channel + 3 * (Person->Msg + Person->Team + Msg->Chan + Msg->Doc) = 1 + 12 = 13 rels
        self.assertEqual(len(candidate["relationships"]), 13)

    def test_correct_node_labels(self) -> None:
        candidate = build_candidate_document(self.sample_document)
        node_labels = {node["label"] for node in candidate["nodes"]}

        expected_labels = {"Document", "Channel", "Message", "Person", "Team"}
        self.assertEqual(node_labels, expected_labels)

        # Verify Document node properties
        doc_nodes = [n for n in candidate["nodes"] if n["label"] == "Document"]
        self.assertEqual(len(doc_nodes), 1)
        self.assertEqual(
            doc_nodes[0]["document_id"], self.sample_document["document_id"]
        )
        self.assertEqual(doc_nodes[0]["source"], "slack")

        # Verify Channel node properties
        channel_nodes = [
            n for n in candidate["nodes"] if n["label"] == "Channel"
        ]
        self.assertEqual(len(channel_nodes), 1)
        self.assertEqual(channel_nodes[0]["name"], "support")

        # Verify Person nodes
        person_nodes = [n for n in candidate["nodes"] if n["label"] == "Person"]
        person_names = {p["name"] for p in person_nodes}
        self.assertEqual(person_names, {"alex", "sam", "elaine"})

        # Verify Team nodes
        team_nodes = [n for n in candidate["nodes"] if n["label"] == "Team"]
        team_names = {t["name"] for t in team_nodes}
        self.assertEqual(team_names, {"support", "eng-runtime", "eng-sre"})

    def test_correct_relationship_types(self) -> None:
        candidate = build_candidate_document(self.sample_document)
        rel_types = {rel["type"] for rel in candidate["relationships"]}

        expected_rel_types = {
            "IN_CHANNEL",
            "AUTHORED",
            "MEMBER_OF",
            "PART_OF",
        }
        self.assertEqual(rel_types, expected_rel_types)

        # Verify Document -> Channel
        doc_channel_rels = [
            r
            for r in candidate["relationships"]
            if r["from"]["label"] == "Document"
            and r["to"]["label"] == "Channel"
        ]
        self.assertEqual(len(doc_channel_rels), 1)
        self.assertEqual(doc_channel_rels[0]["type"], "IN_CHANNEL")

        # Verify Person -> Message AUTHORED
        authored_rels = [
            r
            for r in candidate["relationships"]
            if r["type"] == "AUTHORED"
        ]
        self.assertEqual(len(authored_rels), 3)
        for rel in authored_rels:
            self.assertEqual(rel["from"]["label"], "Person")
            self.assertEqual(rel["to"]["label"], "Message")

        # Verify Person -> Team MEMBER_OF
        member_rels = [
            r
            for r in candidate["relationships"]
            if r["type"] == "MEMBER_OF"
        ]
        self.assertEqual(len(member_rels), 3)
        for rel in member_rels:
            self.assertEqual(rel["from"]["label"], "Person")
            self.assertEqual(rel["to"]["label"], "Team")

        # Verify Message -> Channel IN_CHANNEL
        msg_channel_rels = [
            r
            for r in candidate["relationships"]
            if r["type"] == "IN_CHANNEL"
            and r["from"]["label"] == "Message"
        ]
        self.assertEqual(len(msg_channel_rels), 3)

        # Verify Message -> Document PART_OF
        part_of_rels = [
            r
            for r in candidate["relationships"]
            if r["type"] == "PART_OF"
        ]
        self.assertEqual(len(part_of_rels), 3)
        for rel in part_of_rels:
            self.assertEqual(rel["from"]["label"], "Message")
            self.assertEqual(rel["to"]["label"], "Document")

    def test_message_ordering_and_text_preserved(self) -> None:
        candidate = build_candidate_document(self.sample_document)
        msg_nodes = [
            n for n in candidate["nodes"] if n["label"] == "Message"
        ]

        # Verify ordering
        message_indices = [m["message_index"] for m in msg_nodes]
        self.assertEqual(message_indices, [1, 2, 3])

        # Verify text and author preservation
        self.assertEqual(
            msg_nodes[0]["text"],
            "Heads-up — ACME reporting p99 API latency ~3x since ~18:30 UTC yesterday.",
        )
        self.assertEqual(msg_nodes[0]["author"], "alex")
        self.assertEqual(msg_nodes[0]["team"], "support")

        self.assertEqual(
            msg_nodes[1]["text"],
            "looking. Can you paste a sample request id / trace?",
        )
        self.assertEqual(msg_nodes[1]["author"], "sam")
        self.assertEqual(msg_nodes[1]["team"], "eng-runtime")

        self.assertEqual(
            msg_nodes[2]["text"],
            "Metrics show request_queue_length for region us-west-2 jumped from 40 -> 410.",
        )
        self.assertEqual(msg_nodes[2]["author"], "elaine")
        self.assertEqual(msg_nodes[2]["team"], "eng-sre")

    def test_repeated_execution_produces_identical_output(self) -> None:
        run_1 = build_candidate_document(self.sample_document)
        run_2 = build_candidate_document(self.sample_document)

        json_1 = json.dumps(run_1, sort_keys=True)
        json_2 = json.dumps(run_2, sort_keys=True)

        self.assertEqual(json_1, json_2)


if __name__ == "__main__":
    unittest.main()
