from __future__ import annotations

import json

import httpx
import pytest
import respx
from tests.data import BASE, BATCH_ENV, HEALTH, VIDEO_ENV, video_list

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


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRANSCRIPTFETCH_API_KEY", raising=False)
    with pytest.raises(ValueError):
        TranscriptFetch()
