"""Client configuration resolution (shared by the sync and async clients)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_BASE_URL = "https://transcriptfetch.com"
ENV_API_KEY = "TRANSCRIPTFETCH_API_KEY"


@dataclass
class ClientConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    timeout: float = 30.0
    max_retries: int = 2


def resolve_config(
    api_key: Optional[str],
    base_url: Optional[str],
    timeout: float,
    max_retries: int,
) -> ClientConfig:
    key = api_key or os.environ.get(ENV_API_KEY)
    if not key:
        raise ValueError(
            "No API key provided. Pass api_key=... or set the "
            f"{ENV_API_KEY} environment variable."
        )
    return ClientConfig(
        api_key=key,
        base_url=(base_url or DEFAULT_BASE_URL).rstrip("/"),
        timeout=timeout,
        max_retries=max(0, max_retries),
    )
