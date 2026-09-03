from __future__ import annotations

import httpx
import pytest
import respx

from tests.data import BASE, VIDEO_ENV, error_env
from transcriptfetch import (
    AuthenticationError,
    IdempotencyConflictError,
    InsufficientCreditsError,
    InternalServerError,
    InvalidRequestError,
    RateLimitError,
    TranscriptFetch,
    UnprocessableInputError,
    UpstreamUnavailableError,
)
from transcriptfetch.errors import APIError


def _client(max_retries: int = 0) -> TranscriptFetch:
    return TranscriptFetch(api_key="k", base_url=BASE, max_retries=max_retries)


@pytest.mark.parametrize(
    "status,code,exc",
    [
        (401, "unauthorized", AuthenticationError),
        (402, "insufficient_credits", InsufficientCreditsError),
        (400, "invalid_request", InvalidRequestError),
        (409, "idempotency_conflict", IdempotencyConflictError),
        (502, "upstream_unavailable", UpstreamUnavailableError),
        (500, "internal_error", InternalServerError),
    ],
)
@respx.mock
def test_error_code_maps_to_exception(status: int, code: str, exc: type[APIError]) -> None:
    respx.post(f"{BASE}/api/v2/transcripts/video").mock(
        return_value=httpx.Response(status, json=error_env(code))
    )
    with _client() as tf, pytest.raises(exc) as info:
        tf.transcripts.video("x")
    assert info.value.code == code
    assert info.value.status == status
    assert info.value.request_id == "req_err"


@respx.mock
def test_invalid_request_carries_issues() -> None:
    issues = [{"path": "video", "message": "required"}]
    respx.post(f"{BASE}/api/v2/transcripts/video").mock(
        return_value=httpx.Response(400, json=error_env("invalid_request", "bad", issues))
    )
    with _client() as tf, pytest.raises(InvalidRequestError) as info:
        tf.transcripts.video("")
    assert info.value.issues == issues


@respx.mock
def test_rate_limit_exposes_retry_after() -> None:
    respx.post(f"{BASE}/api/v2/transcripts/video").mock(
        return_value=httpx.Response(
            429, headers={"retry-after": "2"}, json=error_env("rate_limited")
        )
    )
    with _client() as tf, pytest.raises(RateLimitError) as info:
        tf.transcripts.video("x")
    assert info.value.retry_after == 2.0


@respx.mock
def test_failed_job_raises_rather_than_returning_a_transcript() -> None:
    # A failed job is HTTP 200 with ok:false, so the envelope parser decides it
    # is an error. Assert that, because the alternative would be a Transcript
    # that silently has no text.
    respx.get(f"{BASE}/api/v2/transcripts/jobs/asr_1").mock(
        return_value=httpx.Response(200, json=error_env("no_speech", "No speech was detected."))
    )
    with _client() as tf, pytest.raises(UnprocessableInputError) as info:
        tf.transcripts.job("asr_1")
    assert info.value.code == "no_speech"
    assert info.value.number == 4105
    assert info.value.docs == "https://transcriptfetch.com/docs/errors/no_speech"
    assert info.value.retryable is False


@respx.mock
def test_unprocessable_input_exposes_retry_with() -> None:
    # 4xxx content failures map by family even when the code is not listed,
    # and carry the request change that would succeed.
    body = error_env("no_captions", "No caption track is available for this video.")
    body["error"]["retry_with"] = {"mode": "audio"}
    respx.post(f"{BASE}/api/v2/transcripts/video").mock(
        return_value=httpx.Response(422, json=body)
    )
    with _client() as tf, pytest.raises(UnprocessableInputError) as info:
        tf.transcripts.video("x")
    assert info.value.number == 4103
    assert info.value.retry_with == {"mode": "audio"}
    assert info.value.retryable is False


@respx.mock
def test_transient_family_is_retryable() -> None:
    respx.post(f"{BASE}/api/v2/transcripts/video").mock(
        return_value=httpx.Response(
            503, json=error_env("upstream_error", "The upstream fetch failed.")
        )
    )
    with _client() as tf, pytest.raises(UpstreamUnavailableError) as info:
        tf.transcripts.video("x")
    assert info.value.number == 5001
    assert info.value.retryable is True


@respx.mock
def test_retries_then_succeeds() -> None:
    respx.post(f"{BASE}/api/v2/transcripts/video").mock(
        side_effect=[
            httpx.Response(429, headers={"retry-after": "0"}, json=error_env("rate_limited")),
            httpx.Response(200, json=VIDEO_ENV),
        ]
    )
    with _client(max_retries=1) as tf:
        t = tf.transcripts.video("x")
    assert t.text == "hello world"
