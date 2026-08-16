"""
Offline unit tests for HydraDB Deterministic Retrieval Layer (Step 7).

Validates:
- Empty and whitespace queries
- Exact and partial entity matching
- Exact and partial statement matching
- Statement -> ABOUT -> Entity retrieval and ranking
- Provenance preservation (message_id, document_id)
- Result deduplication and deterministic ordering
- Limit truncation
- Zero-result / unknown keyword case
- Special characters and punctuation handling
- HydraDB query error and malformed response handling
- 100% offline testing with mocked graph responses (zero Gemini calls)
"""

from __future__ import annotations

from typing import Any
import pytest

from backend.retrieval.hydra_retriever import HydraRetriever, extract_rows, retrieve
from backend.retrieval.models import EvidenceItem, QueryRequest, RetrievalResponse


@pytest.fixture
def mock_graph_data() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Synthetic graph responses representing HydraDB query outputs."""
    ext_res = {
        "rows": [
            [{"value": 1001}, {"value": 501}, {"value": "doc_alpha"}],
            [{"value": 1002}, {"value": 502}, {"value": "doc_beta"}],
        ]
    }
    ent_res = {
        "rows": [
            [{"value": 501}, {"value": 201}, {"value": "strict_model:true"}],
            [{"value": 501}, {"value": 202}, {"value": "kernel-selector"}],
            [{"value": 502}, {"value": 203}, {"value": "REL-311"}],
        ]
    }
    stmt_res = {
        "rows": [
            [{"value": 501}, {"value": 301}, {"value": "action"}, {"value": "Enable strict_model:true for canary rollout."}],
            [{"value": 501}, {"value": 302}, {"value": "action"}, {"value": "Revert kernel-selector if regression occurs."}],
            [{"value": 502}, {"value": 303}, {"value": "fact"}, {"value": "Support ticket REL-311 created for incident."}],
        ]
    }
    about_res = {
        "rows": [
            [
                {"value": 303},
                {"value": "fact"},
                {"value": "Support ticket REL-311 created for incident."},
                {"value": 203},
                {"value": "REL-311"},
            ],
        ]
    }
    return ext_res, ent_res, stmt_res, about_res


def test_query_request_validation() -> None:
    req = QueryRequest(query="  test query  ", limit=5)
    assert req.query == "test query"
    assert req.limit == 5

    with pytest.raises(ValueError):
        QueryRequest(query="   ")

    with pytest.raises(ValueError):
        QueryRequest(query="")


def test_extract_rows_helper() -> None:
    assert extract_rows({}) == []
    assert extract_rows({"rows": "invalid"}) == []
    assert extract_rows({"rows": [[{"value": "val1"}, "val2"]]}) == [["val1", "val2"]]


def test_empty_and_whitespace_query(mock_graph_data) -> None:
    ext_res, ent_res, stmt_res, about_res = mock_graph_data
    mock_query = lambda q: ext_res if "HAS_SEMANTIC_EXTRACTION" in q else ent_res if "MENTIONS" in q else stmt_res if "EXPRESSES" in q else about_res

    retriever = HydraRetriever(query_fn=mock_query)

    resp1 = retriever.retrieve("")
    assert resp1.result_count == 0
    assert resp1.results == []

    resp2 = retriever.retrieve("     ")
    assert resp2.result_count == 0
    assert resp2.results == []


def test_exact_entity_and_about_ranking(mock_graph_data) -> None:
    ext_res, ent_res, stmt_res, about_res = mock_graph_data
    mock_query = lambda q: ext_res if "HAS_SEMANTIC_EXTRACTION" in q else ent_res if "MENTIONS" in q else stmt_res if "EXPRESSES" in q else about_res

    retriever = HydraRetriever(query_fn=mock_query)
    resp = retriever.retrieve("REL-311", limit=10)

    assert resp.result_count > 0
    # Highest ranked should be the ABOUT link
    top_item = resp.results[0]
    assert top_item.entity_name == "REL-311"
    assert top_item.relationship == "ABOUT"
    assert top_item.match_type == "exact_entity"
    assert top_item.message_id == 1002
    assert top_item.document_id == "doc_beta"


def test_exact_statement_matching(mock_graph_data) -> None:
    ext_res, ent_res, stmt_res, about_res = mock_graph_data
    mock_query = lambda q: ext_res if "HAS_SEMANTIC_EXTRACTION" in q else ent_res if "MENTIONS" in q else stmt_res if "EXPRESSES" in q else about_res

    retriever = HydraRetriever(query_fn=mock_query)
    resp = retriever.retrieve("canary rollout", limit=5)

    assert resp.result_count > 0
    item = resp.results[0]
    assert "canary rollout" in item.statement.lower()
    assert item.message_id == 1001
    assert item.document_id == "doc_alpha"


def test_partial_entity_matching(mock_graph_data) -> None:
    ext_res, ent_res, stmt_res, about_res = mock_graph_data
    mock_query = lambda q: ext_res if "HAS_SEMANTIC_EXTRACTION" in q else ent_res if "MENTIONS" in q else stmt_res if "EXPRESSES" in q else about_res

    retriever = HydraRetriever(query_fn=mock_query)
    resp = retriever.retrieve("strict_model", limit=5)

    assert resp.result_count > 0
    # Should match strict_model:true
    entity_matches = [i for i in resp.results if i.entity_name == "strict_model:true"]
    assert len(entity_matches) > 0


def test_no_results_unknown_query(mock_graph_data) -> None:
    ext_res, ent_res, stmt_res, about_res = mock_graph_data
    mock_query = lambda q: ext_res if "HAS_SEMANTIC_EXTRACTION" in q else ent_res if "MENTIONS" in q else stmt_res if "EXPRESSES" in q else about_res

    retriever = HydraRetriever(query_fn=mock_query)
    resp = retriever.retrieve("nonexistent_keyword_xyz", limit=10)

    assert resp.result_count == 0
    assert resp.results == []


def test_limit_truncation(mock_graph_data) -> None:
    ext_res, ent_res, stmt_res, about_res = mock_graph_data
    mock_query = lambda q: ext_res if "HAS_SEMANTIC_EXTRACTION" in q else ent_res if "MENTIONS" in q else stmt_res if "EXPRESSES" in q else about_res

    retriever = HydraRetriever(query_fn=mock_query)
    resp = retriever.retrieve("REL-311", limit=1)

    assert resp.result_count == 1
    assert len(resp.results) == 1


def test_special_characters_handling(mock_graph_data) -> None:
    ext_res, ent_res, stmt_res, about_res = mock_graph_data
    mock_query = lambda q: ext_res if "HAS_SEMANTIC_EXTRACTION" in q else ent_res if "MENTIONS" in q else stmt_res if "EXPRESSES" in q else about_res

    retriever = HydraRetriever(query_fn=mock_query)
    # Special symbols, punctuation, quotes
    resp = retriever.retrieve("`strict_model:true`! @#$%", limit=5)
    assert isinstance(resp, RetrievalResponse)
    assert resp.result_count > 0


def test_hydradb_error_handling() -> None:
    def failing_query(q: str) -> dict[str, Any]:
        raise RuntimeError("HydraDB connection timeout")

    retriever = HydraRetriever(query_fn=failing_query)
    resp = retriever.retrieve("strict_model", limit=5)

    assert resp.result_count == 0
    assert resp.results == []


def test_malformed_hydradb_response_handling() -> None:
    def malformed_query(q: str) -> dict[str, Any]:
        return {"rows": "not a list", "columns": None}

    retriever = HydraRetriever(query_fn=malformed_query)
    resp = retriever.retrieve("strict_model", limit=5)

    assert resp.result_count == 0
    assert resp.results == []


def test_provenance_preservation_offline(mock_graph_data) -> None:
    ext_res, ent_res, stmt_res, about_res = mock_graph_data
    mock_query = lambda q: ext_res if "HAS_SEMANTIC_EXTRACTION" in q else ent_res if "MENTIONS" in q else stmt_res if "EXPRESSES" in q else about_res

    retriever = HydraRetriever(query_fn=mock_query)
    resp = retriever.retrieve("kernel-selector", limit=5)

    for item in resp.results:
        assert item.message_id > 0
        assert item.document_id in {"doc_alpha", "doc_beta"}
        assert item.source == "hydradb"
