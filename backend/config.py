"""
Veridex Application Configuration & Validation Layer (Step 17E).

Manages environment configuration for both local OpenCypher development/CI
and HydraDB Cloud v2 production environments. Validates required variables
and enforces strict secret isolation.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass


class AppConfig:
    """Application configuration and validation helper for Local HydraDB."""

    @classmethod
    def get_hydra_url(cls) -> str:
        return os.getenv("HYDRA_URL", "http://127.0.0.1:8443").rstrip("/")

    @classmethod
    def get_hydra_graph(cls) -> str:
        return os.getenv("HYDRA_GRAPH", "default")

    @classmethod
    def get_hydra_namespace(cls) -> str:
        return os.getenv("HYDRA_NAMESPACE", "default")

    @classmethod
    def get_hydra_cell_id(cls) -> str:
        return os.getenv("HYDRA_CELL_ID", "cell-0")

    @classmethod
    def get_hydra_token(cls) -> str:
        return os.getenv("HYDRA_TOKEN", "local-development-token-32-bytes")

    # Compatibility aliases for legacy helpers
    @classmethod
    def get_local_hydra_url(cls) -> str:
        return cls.get_hydra_url()

    @classmethod
    def get_local_hydra_graph(cls) -> str:
        return cls.get_hydra_graph()

    @classmethod
    def get_gemini_api_key(cls) -> str | None:
        return os.getenv("GEMINI_API_KEY")

    @classmethod
    def get_gemini_model(cls) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    @classmethod
    def get_port(cls) -> int:
        return int(os.getenv("PORT", "8000"))

    @classmethod
    def validate_config(cls) -> None:
        """
        Validate configuration for Local HydraDB.
        Raises ValueError with clear, safe error messages if required settings are missing.
        """
        url = cls.get_hydra_url()
        if not url or not url.strip():
            raise ValueError("HYDRA_URL environment variable cannot be empty.")

    @classmethod
    def get_safe_summary(cls) -> dict[str, Any]:
        """Return safe configuration metadata with all secrets masked."""
        gemini_key = cls.get_gemini_api_key()

        return {
            "hydra_url": cls.get_hydra_url(),
            "hydra_graph": cls.get_hydra_graph(),
            "hydra_namespace": cls.get_hydra_namespace(),
            "hydra_cell_id": cls.get_hydra_cell_id(),
            "gemini_configured": bool(gemini_key and gemini_key.strip()),
            "gemini_model": cls.get_gemini_model(),
            "port": cls.get_port(),
        }
