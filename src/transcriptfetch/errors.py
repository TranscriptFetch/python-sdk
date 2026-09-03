"""Exception hierarchy for the TranscriptFetch SDK.

The API (v2) returns one error block on every failure::

    { "ok": false, "request_id": "...",
      "error": { "code", "number", "message", "docs", "retry_with"?, "details"?, "issues"? } }

``code`` is a stable string and ``number`` a stable integer whose thousands
digit is the family (1 request, 2 account, 3 input, 4 content, 5 transient,
9 ours). We map ``error.code`` (falling back to the number's family, then the
HTTP status) to a specific exception subclass so callers can branch cleanly,
and expose the rest of the block as attributes.
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
        number: Optional[int] = None,
        request_id: Optional[str] = None,
        docs: Optional[str] = None,
        retry_with: Optional[dict[str, Any]] = None,
        details: Optional[dict[str, Any]] = None,
        issues: Optional[list[Any]] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.number = number
        """Stable numeric code; the thousands digit is the family."""
        self.message = message
        self.request_id = request_id
        self.docs = docs
        """Per-code documentation URL."""
        self.retry_with = retry_with
        """The request change that would succeed, e.g. ``{"mode": "audio"}``, else ``None``."""
        self.details = details
        """Structured specifics for the few codes that document them."""
        self.issues = issues or []

    @property
    def retryable(self) -> bool:
        """Whether the SAME request is worth retrying with backoff.

        True for the transient (5xxx) and server (9xxx) families, plus rate
        limits and credit exhaustion once the condition clears. Never true for
        1xxx/3xxx/4xxx, where the request itself has to change (see
        ``retry_with``).
        """
        if self.number is not None:
            family = self.number // 1000
            return family in (5, 9) or self.code in ("rate_limited", "insufficient_credits")
        return self.status == 429 or self.status >= 500

    def __str__(self) -> str:
        bits = [self.message]
        meta = [f"status={self.status}"]
        if self.code:
            meta.append(f"code={self.code}")
        if self.number is not None:
            meta.append(f"number={self.number}")
        if self.request_id:
            meta.append(f"request_id={self.request_id}")
        bits.append(f"[{', '.join(meta)}]")
        return " ".join(bits)


class AuthenticationError(APIError):
    """401: missing or invalid API key."""


class InvalidRequestError(APIError):
    """400: the request body failed validation (see ``issues``), or a stale cursor."""


class BatchTooLargeError(InvalidRequestError):
    """400 ``batch_too_large``: over your plan's per-batch cap (see ``details["max"]``)."""


class NotFoundError(APIError):
    """404: no such job for this account."""


class InsufficientCreditsError(APIError):
    """402: not enough credits to complete the request."""


class IdempotencyConflictError(APIError):
    """409: Idempotency-Key reused with a different body, or still in flight."""


class RateLimitError(APIError):
    """429: per-key rate limit exceeded."""

    def __init__(self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class UnprocessableInputError(APIError):
    """422: this input cannot be served, permanently (the 3xxx and 4xxx families).

    An unsupported platform, the wrong endpoint for the platform, a podcast
    with no public feed, a private or live video, no captions, no speech.
    ``code`` says which; ``retry_with`` is set when a different request would
    work (e.g. ``{"mode": "audio"}`` to transcribe a captionless video).
    """


class UpstreamUnavailableError(APIError):
    """502/503: the upstream platform blocked or was unreachable. Safe to retry.

    Upstream platform blocks answer 503 with code ``upstream_error``, never
    429, which is reserved for per-key rate limits (:class:`RateLimitError`).
    """


class InternalServerError(APIError):
    """500: unexpected server error."""


_CODE_TO_EXC: dict[str, type[APIError]] = {
    "unauthorized": AuthenticationError,
    "invalid_request": InvalidRequestError,
    "invalid_cursor": InvalidRequestError,
    "not_found": NotFoundError,
    "insufficient_credits": InsufficientCreditsError,
    "batch_too_large": BatchTooLargeError,
    "idempotency_conflict": IdempotencyConflictError,
    "rate_limited": RateLimitError,
    "upstream_unavailable": UpstreamUnavailableError,
    "internal_error": InternalServerError,
}

_STATUS_TO_EXC: dict[int, type[APIError]] = {
    400: InvalidRequestError,
    401: AuthenticationError,
    402: InsufficientCreditsError,
    404: NotFoundError,
    409: IdempotencyConflictError,
    422: UnprocessableInputError,
    429: RateLimitError,
    500: InternalServerError,
    502: UpstreamUnavailableError,
    503: UpstreamUnavailableError,
}


def _exc_for(code: Optional[str], number: Optional[int], status: int) -> type[APIError]:
    """Choose the class from the number's family when the code is not listed."""
    if code and code in _CODE_TO_EXC:
        return _CODE_TO_EXC[code]
    if number is not None:
        family = number // 1000
        if family in (3, 4):
            return UnprocessableInputError
        if family == 5:
            return UpstreamUnavailableError
        if family == 9:
            return InternalServerError
    return _STATUS_TO_EXC.get(status, APIError)


def raise_api_error(
    status: int,
    payload: dict[str, Any],
    request_id: Optional[str],
    retry_after: Optional[str] = None,
) -> NoReturn:
    """Map an error response to the appropriate exception and raise it."""
    error = payload.get("error") if isinstance(payload, dict) else None
    code: Optional[str] = None
    number: Optional[int] = None
    message = f"Request failed with status {status}"
    docs: Optional[str] = None
    retry_with: Optional[dict[str, Any]] = None
    details: Optional[dict[str, Any]] = None
    issues: Optional[list[Any]] = None
    if isinstance(error, dict):
        code = error.get("code")
        raw_number = error.get("number")
        number = raw_number if isinstance(raw_number, int) else None
        message = error.get("message") or message
        docs = error.get("docs") if isinstance(error.get("docs"), str) else None
        retry_with = error.get("retry_with") if isinstance(error.get("retry_with"), dict) else None
        details = error.get("details") if isinstance(error.get("details"), dict) else None
        raw_issues = error.get("issues")
        if isinstance(raw_issues, list):
            issues = raw_issues

    exc_cls = _exc_for(code, number, status)
    kwargs: dict[str, Any] = dict(
        status=status,
        code=code,
        number=number,
        request_id=request_id,
        docs=docs,
        retry_with=retry_with,
        details=details,
        issues=issues,
    )

    if exc_cls is RateLimitError:
        parsed_retry: Optional[float] = None
        if retry_after is not None:
            try:
                parsed_retry = float(retry_after)
            except (TypeError, ValueError):
                parsed_retry = None
        raise RateLimitError(message, retry_after=parsed_retry, **kwargs)

    raise exc_cls(message, **kwargs)
