"""Exception hierarchy for the TranscriptFetch SDK.

The API returns a canonical error envelope: ``{ ok: false, request_id, error:
{ code, message, issues? } }``. We map ``error.code`` (falling back to the HTTP
status) to a specific exception subclass so callers can branch cleanly.
"""

from __future__ import annotations

from typing import Any, NoReturn, Optional


class TranscriptFetchError(Exception):
    """Base class for every error raised by this SDK."""


class APIConnectionError(TranscriptFetchError):
    """A network problem prevented the request from completing (DNS/TLS/connect)."""


class APITimeoutError(APIConnectionError):
    """The request did not complete within the configured timeout."""


class APIError(TranscriptFetchError):
    """The API returned an error response."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        issues: Optional[list[Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.request_id = request_id
        self.issues = issues or []

    def __str__(self) -> str:
        bits = [self.message]
        meta = [f"status={self.status}"]
        if self.code:
            meta.append(f"code={self.code}")
        if self.request_id:
            meta.append(f"request_id={self.request_id}")
        bits.append(f"[{', '.join(meta)}]")
        return " ".join(bits)


class AuthenticationError(APIError):
    """401: missing or invalid API key."""


class InvalidRequestError(APIError):
    """400: the request body failed validation (see ``issues``)."""


class InsufficientCreditsError(APIError):
    """402: not enough credits to complete the request."""


class IdempotencyConflictError(APIError):
    """409: Idempotency-Key reused with a different body, or still in flight."""


class RateLimitError(APIError):
    """429: per-key rate limit exceeded."""

    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class UpstreamUnavailableError(APIError):
    """502: the upstream transcript service was unreachable. Safe to retry."""


class InternalServerError(APIError):
    """500: unexpected server error."""


_CODE_TO_EXC: dict[str, type[APIError]] = {
    "unauthorized": AuthenticationError,
    "invalid_request": InvalidRequestError,
    "insufficient_credits": InsufficientCreditsError,
    "idempotency_conflict": IdempotencyConflictError,
    "rate_limited": RateLimitError,
    "upstream_unavailable": UpstreamUnavailableError,
    "internal_error": InternalServerError,
}

_STATUS_TO_EXC: dict[int, type[APIError]] = {
    400: InvalidRequestError,
    401: AuthenticationError,
    402: InsufficientCreditsError,
    409: IdempotencyConflictError,
    429: RateLimitError,
    500: InternalServerError,
    502: UpstreamUnavailableError,
    503: UpstreamUnavailableError,
}


def raise_api_error(
    status: int,
    payload: dict[str, Any],
    request_id: Optional[str],
    retry_after: Optional[str] = None,
) -> NoReturn:
    """Map an error response to the appropriate exception and raise it."""
    error = payload.get("error") if isinstance(payload, dict) else None
    code: Optional[str] = None
    message = f"Request failed with status {status}"
    issues: Optional[list[Any]] = None
    if isinstance(error, dict):
        code = error.get("code")
        message = error.get("message") or message
        raw_issues = error.get("issues")
        if isinstance(raw_issues, list):
            issues = raw_issues

    exc_cls = (code and _CODE_TO_EXC.get(code)) or _STATUS_TO_EXC.get(status) or APIError

    if exc_cls is RateLimitError:
        parsed_retry: Optional[float] = None
        if retry_after is not None:
            try:
                parsed_retry = float(retry_after)
            except (TypeError, ValueError):
                parsed_retry = None
        raise RateLimitError(
            message,
            status=status,
            code=code,
            request_id=request_id,
            issues=issues,
            retry_after=parsed_retry,
        )

    raise exc_cls(message, status=status, code=code, request_id=request_id, issues=issues)
