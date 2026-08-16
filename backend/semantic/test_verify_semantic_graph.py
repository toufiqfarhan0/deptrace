"""
Unit tests for Step 6J count-independent semantic graph verification.

Validates:
- Scalar count parsing for integer cells
- Count-independent invariant assertions (0, 7, 9, 20, 50, 100 items)
- Detection of provenance mismatches
- Discrepancy detection between COUNT(*) and traversed relationship count
- Statement -> ABOUT -> Entity relationship count verification
- 100% offline testing with mocked query engine
"""

from __future__ import annotations

from unittest.mock import patch
import pytest

from backend.semantic.verify_semantic_graph import (
    extract_scalar_count,
    verify_semantic_graph,
)


def test_extract_scalar_count() -> None:
    # Formatted HydraDB dictionary cell
    res1 = {"rows": [[{"type": "integer", "value": 42}]]}
    assert extract_scalar_count(res1) == 42

    # Raw integer cell
    res2 = {"rows": [[99]]}
    assert extract_scalar_count(res2) == 99

    # Empty result
    assert extract_scalar_count({"rows": []}) == 0
    assert extract_scalar_count({}) == 0


def test_verify_semantic_graph_mocked_invariants_arbitrary_sizes() -> None:
    """Test that the verifier accepts any valid count (e.g. 9, 20, 100) without hard-coded limits."""
    for count in [0, 7, 9, 20, 50, 100]:
        mock_extractions_count = {"rows": [[{"type": "integer", "value": count}]]}
        mock_extractions_rows = {
            "rows": [
                [
                    {"value": 1000 + i},
                    {"value": 1000 + i},
                    {"value": f"doc_{1000 + i}"},
                ]
                for i in range(count)
            ]
        }
        mock_entities_count = {"rows": [[{"type": "integer", "value": count * 2}]]}
        mock_entities_rows = {
            "rows": [[{"value": 2000 + i}, {"value": f"Entity-{i}"}] for i in range(min(count * 2, 20))]
        }
        mock_stmts_count = {"rows": [[{"type": "integer", "value": count * 3}]]}
        mock_stmts_rows = {
            "rows": [[{"value": "fact"}, {"value": f"Statement {i}"}] for i in range(min(count * 3, 20))]
        }
        mock_about_count = {"rows": [[{"type": "integer", "value": count * 4}]]}
        mock_about_rows = {
            "rows": [
                [{"value": 3000 + i}, {"value": f"Statement {i}"}, {"value": f"Entity-{i}"}]
                for i in range(min(count * 4, 20))
            ]
        }

        with patch("backend.semantic.verify_semantic_graph.query") as mock_q:
            mock_q.side_effect = [
                mock_extractions_count,
                mock_extractions_rows,
                mock_entities_count,
                mock_entities_rows,
                mock_stmts_count,
                mock_stmts_rows,
                mock_about_count,
                mock_about_rows,
            ]

            stats = verify_semantic_graph()
            assert stats["extractions"] == count
            assert stats["entities"] == count * 2
            assert stats["statements"] == count * 3
            assert stats["about_links"] == count * 4
            assert stats["provenance_errors"] == 0


def test_verify_semantic_graph_catches_provenance_errors() -> None:
    """Test that the verifier rejects provenance mismatches."""
    mock_extractions_count = {"rows": [[{"type": "integer", "value": 1}]]}
    mock_extractions_rows = {
        "rows": [
            [
                {"value": 1001},
                {"value": 9999},  # Mismatched message_id!
                {"value": "doc_1001"},
            ]
        ]
    }
    mock_entities_count = {"rows": [[{"type": "integer", "value": 0}]]}
    mock_entities_rows = {"rows": []}
    mock_stmts_count = {"rows": [[{"type": "integer", "value": 0}]]}
    mock_stmts_rows = {"rows": []}
    mock_about_count = {"rows": [[{"type": "integer", "value": 0}]]}
    mock_about_rows = {"rows": []}

    with patch("backend.semantic.verify_semantic_graph.query") as mock_q:
        mock_q.side_effect = [
            mock_extractions_count,
            mock_extractions_rows,
            mock_entities_count,
            mock_entities_rows,
            mock_stmts_count,
            mock_stmts_rows,
            mock_about_count,
            mock_about_rows,
        ]

        with pytest.raises(AssertionError, match="Expected 0 provenance errors"):
            verify_semantic_graph()


def test_verify_semantic_graph_catches_count_mismatch() -> None:
    """Test that the verifier rejects discrepancies between COUNT(*) and traversed rows."""
    mock_extractions_count = {"rows": [[{"type": "integer", "value": 10}]]}  # Reports 10
    mock_extractions_rows = {
        "rows": [
            [
                {"value": 1001},
                {"value": 1001},
                {"value": "doc_1001"},
            ]
        ]  # But only 1 returned!
    }
    mock_entities_count = {"rows": [[{"type": "integer", "value": 0}]]}
    mock_entities_rows = {"rows": []}
    mock_stmts_count = {"rows": [[{"type": "integer", "value": 0}]]}
    mock_stmts_rows = {"rows": []}
    mock_about_count = {"rows": [[{"type": "integer", "value": 0}]]}
    mock_about_rows = {"rows": []}

    with patch("backend.semantic.verify_semantic_graph.query") as mock_q:
        mock_q.side_effect = [
            mock_extractions_count,
            mock_extractions_rows,
            mock_entities_count,
            mock_entities_rows,
            mock_stmts_count,
            mock_stmts_rows,
            mock_about_count,
            mock_about_rows,
        ]

        with pytest.raises(AssertionError, match="does not match traversed rows"):
            verify_semantic_graph()
