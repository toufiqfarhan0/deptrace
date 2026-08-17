"""
Production Deployment Readiness & Secret Isolation Tests (Step 17E).

Tests configuration validation, driver switching, secret isolation in frontend bundles,
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
from backend.retrieval.cloud_retriever import HydraCloudRetriever
from backend.retrieval.cloud_tracer import HydraCloudTracer
from backend.retrieval.hydra_retriever import HydraRetriever
from backend.retrieval.dependency_tracer import DependencyTracer

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_local_mode_default_configuration() -> None:
    """Verify local mode is the default and does not require Cloud API keys."""
    with patch.dict(os.environ, {"HYDRA_MODE": "local"}, clear=False):
        assert AppConfig.get_hydra_mode() == "local"
        # Should not raise ValueError even if HYDRA_DB_API_KEY is empty
        with patch.dict(os.environ, {"HYDRA_DB_API_KEY": ""}, clear=False):
            AppConfig.validate_config()
            retriever = get_active_retriever()
            tracer = get_active_tracer()
            assert isinstance(retriever, HydraRetriever)
            assert isinstance(tracer, DependencyTracer)


def test_cloud_mode_configuration_validation() -> None:
    """Verify cloud mode validates required server-side secrets and configuration."""
    # 1. Missing API key fails clearly
    with patch.dict(os.environ, {"HYDRA_MODE": "cloud", "HYDRA_DB_API_KEY": ""}, clear=False):
        with pytest.raises(ValueError, match="HYDRA_DB_API_KEY environment variable is required"):
            AppConfig.validate_config()

    # 2. Valid Cloud configuration instantiates Cloud drivers
    with patch.dict(
        os.environ,
        {
            "HYDRA_MODE": "cloud",
            "HYDRA_DB_API_KEY": "test_cloud_secret_token",
            "HYDRA_DB_DATABASE": "veridex-hackhydra",
        },
        clear=False,
    ):
        AppConfig.validate_config()
        retriever = get_active_retriever()
        tracer = get_active_tracer()
        assert isinstance(retriever, HydraCloudRetriever)
        assert isinstance(tracer, HydraCloudTracer)


def test_health_check_does_not_expose_secrets(client: TestClient) -> None:
    """Verify health endpoint never returns API keys or secret tokens."""
    # Test local mode health
    with patch.dict(os.environ, {"HYDRA_MODE": "local"}):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "hydradb" in data
        # No secret field in JSON
        assert "api_key" not in data
        assert "token" not in data
        assert "key" not in data

    # Test cloud mode health with mock
    with patch.dict(os.environ, {"HYDRA_MODE": "cloud", "HYDRA_DB_API_KEY": "secret_key_123"}):
        with patch.object(
            HydraCloudRetriever,
            "check_health",
            return_value={"status": "ok", "hydradb": "ok (cloud: veridex-hackhydra)"},
        ):
            res = client.get("/api/health")
            assert res.status_code == 200
            assert "secret_key_123" not in res.text


def test_safe_config_summary_redaction() -> None:
    """Verify AppConfig.get_safe_summary masks secrets."""
    with patch.dict(
        os.environ,
        {
            "HYDRA_MODE": "cloud",
            "HYDRA_DB_API_KEY": "super_secret_hydra_token",
            "GEMINI_API_KEY": "super_secret_gemini_token",
        },
    ):
        summary = AppConfig.get_safe_summary()
        summary_str = str(summary)
        assert "super_secret_hydra_token" not in summary_str
        assert "super_secret_gemini_token" not in summary_str
        assert summary["cloud_key_configured"] is True
        assert summary["gemini_configured"] is True


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
        # Skip node_modules
        if "node_modules" in dirs:
            dirs.remove("node_modules")

        for f in files:
            if f.endswith((".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json")):
                file_path = Path(root) / f
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for pat in forbidden_patterns:
                    assert pat not in content, f"Forbidden secret identifier '{pat}' found in {file_path}"
                scanned_files += 1

    assert scanned_files > 0, "No frontend files were scanned"


def test_cloud_retriever_clean_chunk_text() -> None:
    """Verify clean_chunk_text extracts text from diverse Cloud chunk formats."""
    retriever = HydraCloudRetriever(api_key="mock_key")

    # Case 1: Complete JSON with content.text
    json_full = '{"id":"dsid_123","title":"Ticket","content":{"text":"Complete body of the ticket."}}'
    assert retriever.clean_chunk_text(json_full) == "Complete body of the ticket."

    # Case 2: JSON fragment containing "content":{"text":"..."}
    json_frag = '{"id":"dsid_123","content":{"text":"Fragment of discussion text with \\"quotes\\" and \\u003e arrow.'
    cleaned = retriever.clean_chunk_text(json_frag)
    assert "Fragment of discussion text" in cleaned
    assert ">" in cleaned

    # Case 3: JSON fragment with trailing metadata
    json_trailing = 'Plain text body of the PR description.", "html_base64":"","tenant_metadata":{"source":"github"}'
    assert retriever.clean_chunk_text(json_trailing) == 'Plain text body of the PR description.'

    # Case 4: Plain text
    plain = "Direct plain text statement from Slack conversation."
    assert retriever.clean_chunk_text(plain) == plain


def test_cloud_retriever_extract_identifiers() -> None:
    """Verify extract_identifiers identifies PRs, tickets, incidents, and channels."""
    retriever = HydraCloudRetriever(api_key="mock_key")
    tokens = retriever.extract_identifiers("What happened during incident INC-2026 and PR-99501 for Bluecrest in #incidents?")
    assert "INC-2026" in tokens
    assert "PR-99501" in tokens
    assert "Bluecrest" in tokens
    assert "#incidents" in tokens
