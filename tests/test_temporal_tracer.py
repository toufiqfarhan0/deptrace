"""
Unit tests for Temporal Knowledge Graph & Incident Timeline Tracer (Step 18).
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.app import app
from backend.retrieval.temporal_tracer import (
    TemporalTracer,
    classify_event_phase,
    format_delta_time,
    parse_timestamp_str,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_timestamp_parsing():
    dt1 = parse_timestamp_str("2026-03-12T14:22:00Z")
    assert dt1 is not None
    assert dt1.year == 2026
    assert dt1.month == 3
    assert dt1.day == 12

    dt2 = parse_timestamp_str("2026-03-12 14:22:00")
    assert dt2 is not None

    assert parse_timestamp_str(None) is None
    assert parse_timestamp_str("") is None


def test_delta_time_formatting():
    assert format_delta_time(0) == "+0m"
    assert format_delta_time(300) == "+5m"
    assert format_delta_time(3600) == "+1h"
    assert format_delta_time(4500) == "+1h 15m"


def test_phase_classification():
    p1, _ = classify_event_phase("slack", "Alert: Memory pressure", "OOM error spike", 1, 4)
    assert p1 == "detection"

    p2, _ = classify_event_phase("linear", "Root cause triage", "Investigating kernel-selector", 2, 4)
    assert p2 == "investigation"

    p3, _ = classify_event_phase("github", "Hotfix: Revert fallback policy", "PR mitigation", 3, 4)
    assert p3 == "mitigation"

    p4, _ = classify_event_phase("slack", "Incident resolved and verified", "SLA restored", 4, 4)
    assert p4 == "resolution"


def test_temporal_tracer_featured_incidents():
    tracer = TemporalTracer()
    incidents = tracer.get_featured_incidents()
    assert len(incidents) >= 4
    inc_ids = [i["id"] for i in incidents]
    assert "INC-2026" in inc_ids
    assert "REL-311" in inc_ids
    assert "PR-99501" in inc_ids


def test_temporal_tracer_build_timeline():
    tracer = TemporalTracer()
    res = tracer.build_timeline("INC-2026")
    assert res.found is True
    assert res.target_entity == "INC-2026"
    assert res.total_events > 0
    assert len(res.events) == res.total_events
    assert len(res.all_nodes) > 0
    assert len(res.all_edges) > 0

    # Verify event structure
    first_event = res.events[0]
    assert first_event.order == 1
    assert first_event.relative_time == "+0m"
    assert bool(first_event.title)
    assert bool(first_event.source)


def test_temporal_tracer_empty_entity():
    tracer = TemporalTracer()
    res = tracer.build_timeline("   ")
    assert res.found is False
    assert res.error is not None


def test_api_timeline_endpoints(client):
    # 1. Test GET /api/timeline/incidents
    res_inc = client.get("/api/timeline/incidents")
    assert res_inc.status_code == 200
    data_inc = res_inc.json()
    assert isinstance(data_inc, list)
    assert len(data_inc) >= 4

    # 2. Test GET /api/timeline?entity=INC-2026
    res_tl = client.get("/api/timeline?entity=INC-2026")
    assert res_tl.status_code == 200
    data_tl = res_tl.json()
    assert data_tl["found"] is True
    assert data_tl["target_entity"] == "INC-2026"
    assert data_tl["total_events"] >= 1
    assert len(data_tl["events"]) >= 1
    assert len(data_tl["all_nodes"]) >= 1

    # 3. Test GET /api/timeline with another entity
    res_rel = client.get("/api/timeline?entity=REL-311")
    assert res_rel.status_code == 200
    data_rel = res_rel.json()
    assert data_rel["found"] is True
    assert data_rel["target_entity"] == "REL-311"
