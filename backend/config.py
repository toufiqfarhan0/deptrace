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
    """Application configuration and validation helper."""

    @classmethod
    def get_hydra_mode(cls) -> str:
        """Active HydraDB mode: 'local' (default) | 'cloud'."""
        return os.getenv("HYDRA_MODE", "local").strip().lower()

    @classmethod
    def get_local_hydra_url(cls) -> str:
        return os.getenv("HYDRA_URL", "http://127.0.0.1:8443").rstrip("/")

    @classmethod
    def get_local_hydra_graph(cls) -> str:
        return os.getenv("HYDRA_GRAPH", "default")

    @classmethod
    def get_cloud_api_key(cls) -> str | None:
        return os.getenv("HYDRA_DB_API_KEY")

    @classmethod
    def get_cloud_database(cls) -> str:
        return (
            os.getenv("HYDRA_DB_DATABASE")
            or os.getenv("HYDRA_DATABASE")
            or "veridex-hackhydra"
        )

    @classmethod
    def get_cloud_base_url(cls) -> str:
        return (
            os.getenv("HYDRA_DB_BASE_URL")
            or os.getenv("HYDRA_BASE_URL")
            or "https://api.hydradb.com"
        ).rstrip("/")

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
        Validate configuration for the active mode.
        Raises ValueError with clear, safe error messages if required settings are missing.
        """
        mode = cls.get_hydra_mode()
        if mode not in ("local", "cloud"):
            raise ValueError(f"Invalid HYDRA_MODE='{mode}'. Expected 'local' or 'cloud'.")

        if mode == "cloud":
            api_key = cls.get_cloud_api_key()
            if not api_key or not api_key.strip():
                raise ValueError(
                    "HYDRA_DB_API_KEY environment variable is required when HYDRA_MODE='cloud'. "
                    "Set HYDRA_DB_API_KEY in server environment."
                )
            database = cls.get_cloud_database()
            if not database or not database.strip():
                raise ValueError("HYDRA_DB_DATABASE is required when HYDRA_MODE='cloud'.")

    @classmethod
    def get_safe_summary(cls) -> dict[str, Any]:
        """Return safe configuration metadata with all secrets masked."""
        mode = cls.get_hydra_mode()
        cloud_key = cls.get_cloud_api_key()
        gemini_key = cls.get_gemini_api_key()

        return {
            "hydra_mode": mode,
            "local_url": cls.get_local_hydra_url() if mode == "local" else None,
            "local_graph": cls.get_local_hydra_graph() if mode == "local" else None,
            "cloud_database": cls.get_cloud_database() if mode == "cloud" else None,
            "cloud_base_url": cls.get_cloud_base_url() if mode == "cloud" else None,
            "cloud_key_configured": bool(cloud_key and cloud_key.strip()),
            "gemini_configured": bool(gemini_key and gemini_key.strip()),
            "gemini_model": cls.get_gemini_model(),
        }
