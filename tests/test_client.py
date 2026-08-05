from __future__ import annotations

import json

import httpx
import pytest
import respx

from tests.data import (
    BASE,
    BATCH_ENV,
    HEALTH,
    JOB_ACCEPTED_ENV,
    JOB_DONE_ENV,
    JOB_PROCESSING_ENV,
    ME_ENV,
    VIDEO_ENV,
    video_list,
)
from transcriptfetch import TranscriptFetch


def _client() -> TranscriptFetch:
    return TranscriptFetch(api_key="tf_test", base_url=BASE, max_retries=0)


@respx.mock
def test_video_parses_and_sends_headers() -> None:
    route = respx.post(f"{BASE}/api/v1/transcripts/video").mock(
        return_value=httpx.Response(200, json=VIDEO_ENV)
    )
    with _client() as tf:
        t = tf.transcripts.video("dQw4w9WgXcQ")

    assert t.video_id == "abc"
    assert t.text == "hello world"
    assert t.segments[0].text == "hi"
    assert t.usage is not None and t.usage.balance == 99

    req = route.calls.last.request
    assert req.headers["authorization"] == "Bearer tf_test"
    assert req.headers.get("idempotency-key")  # auto-generated
    assert json.loads(req.content)["video"] == "dQw4w9WgXcQ"


@respx.mock
def test_channel_auto_pagination() -> None:
    respx.post(f"{BASE}/api/v1/transcripts/channel").mock(
        side_effect=[
            httpx.Response(200, json=video_list([{"videoId": "a", "title": "A"}], "cur1")),
            httpx.Response(200, json=video_list([{"videoId": "b", "title": "B"}], None)),
        ]
    )
    with _client() as tf:
        ids = [v.video_id for v in tf.transcripts.iter_channel("@x", limit=1)]
    assert ids == ["a", "b"]


@respx.mock
def test_video_list_camelcase_aliases() -> None:
    respx.post(f"{BASE}/api/v1/transcripts/search").mock(
        return_value=httpx.Response(
            200,
            json=video_list(
                [{"videoId": "z", "title": "Z", "thumbnailUrl": "http://t/z.jpg", "channel": "C"}],
                None,
            ),
        )
    )
    with _client() as tf:
        page = tf.transcripts.search("hi")
    v = page.videos[0]
    assert v.video_id == "z"
    assert v.thumbnail_url == "http://t/z.jpg"
    assert v.channel == "C"


@respx.mock
def test_batch() -> None:
    route = respx.post(f"{BASE}/api/v1/transcripts/batch").mock(
        return_value=httpx.Response(200, json=BATCH_ENV)
    )
    with _client() as tf:
        res = tf.transcripts.batch(["a", "b"])
    assert [r.video_id for r in res.results] == ["a", "b"]
    assert res.results[1].outcome == "no_transcript"
    assert json.loads(route.calls.last.request.content)["videoIds"] == ["a", "b"]


@respx.mock
def test_health_is_unauthenticated() -> None:
    route = respx.get(f"{BASE}/api/v1/health").mock(return_value=httpx.Response(200, json=HEALTH))
    with _client() as tf:
        h = tf.health()
    assert h["status"] == "ok"
    assert "authorization" not in route.calls.last.request.headers


@respx.mock
def test_me_returns_balance() -> None:
    route = respx.get(f"{BASE}/api/v1/me").mock(return_value=httpx.Response(200, json=ME_ENV))
    with _client() as tf:
        me = tf.me()
    assert me.user_id == "user_1"
    assert me.credits == 250
    assert me.usage is not None and me.usage.credits_spent == 0
    assert route.calls.last.request.headers["authorization"] == "Bearer tf_test"


@respx.mock
def test_video_without_captions_returns_pollable_job() -> None:
    # A 202 carries kind="transcript_job" and no transcript body; it must not
    # blow up parsing, since polling is the documented path from here.
    respx.post(f"{BASE}/api/v1/transcripts/video").mock(
        return_value=httpx.Response(202, json=JOB_ACCEPTED_ENV)
    )
    respx.get(f"{BASE}/api/v1/transcripts/jobs/asr_1").mock(
        side_effect=[
            httpx.Response(200, json=JOB_PROCESSING_ENV),
            httpx.Response(200, json=JOB_DONE_ENV),
        ]
    )
    with _client() as tf:
        started = tf.transcripts.video("https://www.tiktok.com/@u/video/7137723462233555205")
        assert started.status == "processing"
        assert started.job_id == "asr_1"
        assert started.poll_url == "/api/v1/transcripts/jobs/asr_1"
        assert started.text is None

        assert tf.transcripts.job("asr_1").status == "processing"
        done = tf.transcripts.job("asr_1")

    assert done.status == "completed"
    assert done.text == "hello world"
    assert done.usage is not None and done.usage.balance == 96


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRANSCRIPTFETCH_API_KEY", raising=False)
    with pytest.raises(ValueError):
        TranscriptFetch()
