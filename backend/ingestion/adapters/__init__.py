"""
Source Adapters for Multi-Source Ingestion (Step 13B).
"""

from __future__ import annotations

from backend.ingestion.adapters.base import BaseAdapter
from backend.ingestion.adapters.github_adapter import GitHubAdapter
from backend.ingestion.adapters.linear_adapter import LinearAdapter
from backend.ingestion.adapters.slack_adapter import SlackAdapter


def get_adapter_for_source(source: str) -> BaseAdapter:
    """Return the adapter instance for a given source name."""
    s = source.strip().lower()
    if s == "slack":
        return SlackAdapter()
    elif s == "linear":
        return LinearAdapter()
    elif s == "github":
        return GitHubAdapter()
    raise ValueError(f"Unsupported enterprise source: '{source}'. Expected 'slack', 'linear', or 'github'.")


__all__ = [
    "BaseAdapter",
    "SlackAdapter",
    "LinearAdapter",
    "GitHubAdapter",
    "get_adapter_for_source",
]
