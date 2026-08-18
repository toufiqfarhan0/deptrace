"""
Production Deployment Readiness & Secret Isolation Tests for Local HydraDB.

Tests configuration validation, local driver operation, secret isolation in frontend bundles,
and safe health check responses.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from starlette.testclient import TestClient

from backend.api.app import app
from backend.config import AppConfig
from backend.retrieval.factory import get_active_retriever, get_active_tracer, get_hydra_mode
from backend.retrieval.hydra_retriever import HydraRetriever
from backend.retrieval.dependency_tracer import DependencyTracer

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_local_mode_default_configuration() -> None:
    """Verify local mode is the default and does not require Cloud API keys."""
    assert AppConfig.get_hydra_url() == "http://127.0.0.1:8443"
    assert AppConfig.get_hydra_graph() == "default"
    assert AppConfig.get_hydra_namespace() == "default"
    assert AppConfig.get_hydra_cell_id() == "cell-0"

    AppConfig.validate_config()
    retriever = get_active_retriever()
    tracer = get_active_tracer()
    assert isinstance(retriever, HydraRetriever)
    assert isinstance(tracer, DependencyTracer)


def test_health_check_does_not_expose_secrets(client: TestClient) -> None:
    """Verify health endpoint returns valid local health and never returns secrets."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "hydradb" in data
    # No secret field in JSON
    assert "api_key" not in data
    assert "token" not in data
    assert "key" not in data


def test_safe_config_summary_redaction() -> None:
    """Verify AppConfig.get_safe_summary masks secrets."""
    with patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "super_secret_gemini_token",
        },
    ):
        summary = AppConfig.get_safe_summary()
        summary_str = str(summary)
        assert "super_secret_gemini_token" not in summary_str
        assert summary["gemini_configured"] is True
        assert summary["hydra_url"] == "http://127.0.0.1:8443"


def test_frontend_source_and_bundle_secret_isolation() -> None:
    """Scan frontend source and production bundle for accidental API key exposure."""
    frontend_dir = PROJECT_ROOT / "frontend-react"
    if not frontend_dir.exists():
        pytest.skip("frontend-react directory not found")

    forbidden_patterns = [
        "HYDRA_DB_API_KEY",
        "VITE_HYDRA_DB_API_KEY",
        "VITE_GEMINI_API_KEY",
    ]

    scanned_files = 0
    for root, dirs, files in os.walk(frontend_dir):
        # Skip node_modules and dist
        if "node_modules" in dirs:
            dirs.remove("node_modules")
        if "dist" in dirs:
            dirs.remove("dist")

        for f in files:
            if f.endswith((".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json")):
                file_path = Path(root) / f
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for pat in forbidden_patterns:
                    assert pat not in content, f"Forbidden secret identifier '{pat}' found in {file_path}"
                scanned_files += 1

    assert scanned_files > 0, "No frontend files were scanned"
