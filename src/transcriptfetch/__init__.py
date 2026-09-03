"""Official Python SDK for the TranscriptFetch API.

    from transcriptfetch import TranscriptFetch

    tf = TranscriptFetch(api_key="tf_live_...")   # or set TRANSCRIPTFETCH_API_KEY
    t = tf.transcripts.video("dQw4w9WgXcQ")
    print(t.text, t.usage.balance)
"""

from __future__ import annotations

from ._version import __version__
from .async_client import AsyncTranscriptFetch
from .client import TranscriptFetch
from .errors import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    IdempotencyConflictError,
    BatchTooLargeError,
    InsufficientCreditsError,
    NotFoundError,
    UnprocessableInputError,
    InternalServerError,
    InvalidRequestError,
    RateLimitError,
    TranscriptFetchError,
    UpstreamUnavailableError,
)
from .models import (
    Account,
    BatchResponse,
    ApiErrorBlock,
    BatchResult,
    Podcast,
    Segment,
    Transcript,
    Usage,
    Video,
    VideoList,
)

__all__ = [
    "__version__",
    "TranscriptFetch",
    "AsyncTranscriptFetch",
    # models
    "Usage",
    "Account",
    "Segment",
    "Podcast",
    "Transcript",
    "Video",
    "VideoList",
    "ApiErrorBlock",
    "BatchResult",
    "BatchResponse",
    # errors
    "TranscriptFetchError",
    "APIError",
    "APIConnectionError",
    "APITimeoutError",
    "AuthenticationError",
    "InvalidRequestError",
    "BatchTooLargeError",
    "InsufficientCreditsError",
    "NotFoundError",
    "UnprocessableInputError",
    "IdempotencyConflictError",
    "RateLimitError",
    "UpstreamUnavailableError",
    "InternalServerError",
]
