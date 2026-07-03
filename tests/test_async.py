from __future__ import annotations

import httpx
import respx
from tests.data import BASE, VIDEO_ENV, video_list

from transcriptfetch import AsyncTranscriptFetch


@respx.mock
async def test_async_video() -> None:
    respx.post(f"{BASE}/api/v1/transcripts/video").mock(
        return_value=httpx.Response(200, json=VIDEO_ENV)
    )
    async with AsyncTranscriptFetch(api_key="k", base_url=BASE, max_retries=0) as tf:
        t = await tf.transcripts.video("x")
    assert t.text == "hello world"
    assert t.usage is not None and t.usage.credits_spent == 1


@respx.mock
async def test_async_auto_pagination() -> None:
    respx.post(f"{BASE}/api/v1/transcripts/playlist").mock(
        side_effect=[
            httpx.Response(200, json=video_list([{"videoId": "a"}], "c1")),
            httpx.Response(200, json=video_list([{"videoId": "b"}], None)),
        ]
    )
    async with AsyncTranscriptFetch(api_key="k", base_url=BASE, max_retries=0) as tf:
        ids = [v.video_id async for v in tf.transcripts.iter_playlist("PL", limit=1)]
    assert ids == ["a", "b"]
