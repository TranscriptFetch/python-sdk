"""Shared HTTP helpers used by both the sync and async clients.

The clients own their own httpx client and run the retry loop; this module holds
the pure, transport-agnostic pieces: header building, retry policy, backoff, and
envelope parsing/error mapping.
"""

from __future__ import annotations

import random
import uuid
from typing import Any, Optional

import httpx

from ._config import ClientConfig
from ._version import __version__
from .errors import raise_api_error
from .models import Usage

USER_AGENT = f"transcriptfetch-python/{__version__}"


def build_headers(
    config: ClientConfig,
    idempotency_key: Optional[str],
    *,
    needs_key: bool = True,
) -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if needs_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def parse_usage(env: dict[str, Any]) -> Optional[Usage]:
    """Lift the envelope-level ``usage`` block off a response, if present."""
    raw = env.get("usage")
    return Usage.model_validate(raw) if isinstance(raw, dict) else None


def new_idempotency_key() -> str:
    return uuid.uuid4().hex


def is_retryable(status: int) -> bool:
    return status == 429 or status >= 500


def backoff_seconds(attempt: int, retry_after: Optional[str] = None) -> float:
    if retry_after is not None:
        try:
            return min(float(retry_after), 60.0)
        except (TypeError, ValueError):
            pass
    base: float = min(0.5 * (2**attempt), 8.0)
    return base + random.random() * 0.25


def parse_envelope(response: httpx.Response) -> dict[str, Any]:
    """Return the parsed JSON body, or raise the mapped ``APIError``.

    Handles both the ``{ ok, request_id, data, usage }`` envelope and the bare
    health-check body (which has no ``ok`` field).
    """
    payload: Any
    try:
        payload = response.json()
    except ValueError:
        payload = None

    request_id = payload.get("request_id") if isinstance(payload, dict) else None

    is_error = response.status_code >= 400 or (
        isinstance(payload, dict) and payload.get("ok") is False
    )
    if is_error:
        raise_api_error(
            response.status_code,
            payload if isinstance(payload, dict) else {},
            request_id,
            response.headers.get("retry-after"),
        )

    if not isinstance(payload, dict):
        raise_api_error(response.status_code, {}, request_id, None)

    return payload
