"""
Offline unit tests for python-dotenv support in DeTrace.

Validates:
- Loading environment variables from .env file when not already in os.environ
- Existing os.environ variables take precedence over .env file (override=False)
- Safe handling when .env is absent
- Zero Gemini API calls
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch
import pytest
from dotenv import load_dotenv

from backend.api.app import create_app


def test_dotenv_loads_variables(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TEST_DETRACE_VAR_A=loaded_from_dotenv\nTEST_DETRACE_VAR_B=initial_value\n",
        encoding="utf-8",
    )

    with patch.dict(os.environ, {}, clear=False):
        if "TEST_DETRACE_VAR_A" in os.environ:
            del os.environ["TEST_DETRACE_VAR_A"]
        if "TEST_DETRACE_VAR_B" in os.environ:
            del os.environ["TEST_DETRACE_VAR_B"]

        load_dotenv(dotenv_path=env_file, override=False)
        assert os.environ.get("TEST_DETRACE_VAR_A") == "loaded_from_dotenv"
        assert os.environ.get("TEST_DETRACE_VAR_B") == "initial_value"


def test_dotenv_precedence_existing_env_var(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TEST_DETRACE_PRECEDENCE=from_env_file\n",
        encoding="utf-8",
    )

    with patch.dict(os.environ, {"TEST_DETRACE_PRECEDENCE": "from_process_env"}, clear=False):
        # override=False ensures process environment variable takes precedence
        load_dotenv(dotenv_path=env_file, override=False)
        assert os.environ.get("TEST_DETRACE_PRECEDENCE") == "from_process_env"


def test_dotenv_missing_file_graceful(tmp_path: Path) -> None:
    missing_file = tmp_path / "non_existent.env"
    # Should not raise exception
    loaded = load_dotenv(dotenv_path=missing_file, override=False)
    assert loaded is False


def test_app_initialization_with_dotenv() -> None:
    app = create_app()
    assert app.title == "DeTrace — Enterprise Graph RAG API"
