# TranscriptFetch Python SDK

Official, typed Python client for the [TranscriptFetch](https://transcriptfetch.com) API: fetch transcripts as clean, structured data, plus YouTube channel, playlist and search listings. Sync + async, fully type-hinted.

Transcripts come from **YouTube, TikTok, Instagram, podcasts, or a direct media file URL** (mp3/mp4/wav and friends). A podcast link (a Spotify or Apple Podcasts episode URL, or an RSS feed URL) is resolved to that episode's audio automatically. Channel, playlist and search are YouTube-only, since no other supported platform has those concepts.

```bash
pip install transcriptfetch-sdk
```

## Quickstart

```python
from transcriptfetch import TranscriptFetch

# api_key falls back to the TRANSCRIPTFETCH_API_KEY env var
tf = TranscriptFetch(api_key="tf_live_...")

t = tf.transcripts.video("https://youtu.be/aircAruvnKk")   # or a TikTok / Instagram / podcast / file URL
print(t.title)
print(t.text)
for seg in t.segments:
    print(f"[{seg.start:.1f}] {seg.text}")

print("credits left:", t.usage.balance)
```

Get an API key (100 free credits) at <https://transcriptfetch.com/app>. One credit per successful fetch; failed/blocked/no-transcript requests are free.

## Endpoints

```python
tf.transcripts.video(video)                        # single transcript (text + segments)
tf.transcripts.batch(video_ids)                    # up to 50 transcripts in one call
tf.transcripts.channel(channel, limit=, cursor=)   # a YouTube channel's videos (metadata)
tf.transcripts.playlist(playlist, limit=, cursor=) # a YouTube playlist's videos
tf.transcripts.search(query, limit=, cursor=)      # search YouTube
tf.transcripts.job(job_id)                         # poll an audio-transcription job (free)
tf.me()                                            # validate the key + read the balance (free)
tf.health()                                        # unauthenticated liveness probe
```

`video` and `batch` take a YouTube, TikTok or Instagram URL, a podcast link (Spotify or Apple Podcasts episode, or an RSS feed), a direct media file URL, or a bare YouTube ID. `channel`/`playlist` take a URL, an `@handle`/`PL…` ID, or a raw ID. IDs and URLs are normalized automatically.

## Sources without captions (including every podcast)

When a source has no captions, the API transcribes its audio and answers with a job instead of a transcript. That comes back as a `Transcript` with `status == "processing"` and a `job_id`; poll it for free until it completes. Podcast audio never has captions, so a podcast always takes this path:

```python
import time

t = tf.transcripts.video("https://www.tiktok.com/@user/video/7137723462233555205")
while t.status == "processing":
    time.sleep(3)
    t = tf.transcripts.job(t.job_id)
print(t.text)
```

A transcript resolved from a podcast link also carries a `podcast` block, so the show and episode survive the round trip (otherwise the result would be titled after the mp3 filename):

```python
t = tf.transcripts.video("https://podcasts.apple.com/us/podcast/…")
print(t.platform)          # "podcast"
print(t.podcast.show, "-", t.podcast.episode)
```

## Pagination

List endpoints are cursor-paginated. Iterate every result without managing cursors:

```python
for video in tf.transcripts.iter_channel("@lexfridman", limit=10):
    print(video.video_id, video.title)
```

Or page manually via `page.next_cursor` and the `cursor=` argument.

## Async

```python
import asyncio
from transcriptfetch import AsyncTranscriptFetch

async def main():
    async with AsyncTranscriptFetch() as tf:
        t = await tf.transcripts.video("aircAruvnKk")
        print(t.text)
        async for v in tf.transcripts.iter_search("how transformers work", limit=10):
            print(v.title)

asyncio.run(main())
```

## Errors

All errors subclass `TranscriptFetchError`. API errors carry `.status`, `.code`, `.message`, and `.request_id`:

```python
from transcriptfetch import (
    AuthenticationError, InsufficientCreditsError, InvalidRequestError,
    RateLimitError, IdempotencyConflictError, UpstreamUnavailableError,
    InternalServerError, APIError, APIConnectionError, APITimeoutError,
)

try:
    tf.transcripts.video("bad")
except InsufficientCreditsError:
    ...                       # 402: top up at /pricing
except RateLimitError as e:
    print(e.retry_after)      # 429
except APIError as e:
    print(e.status, e.code, e.request_id)
```

## Reliability

- **Automatic retries** on `429` (honoring `Retry-After`) and `5xx`, with exponential backoff + jitter (`max_retries=2` by default).
- **Idempotency**: every write auto-sends an `Idempotency-Key` so a retried request is never double-charged. Override per call with `idempotency_key=...`.
- **Configurable:** `TranscriptFetch(api_key=..., base_url=..., timeout=30, max_retries=2)`. Both clients are context managers and accept a custom `http_client=` (httpx).

## Development

```bash
pip install -e ".[dev]"
ruff check . && mypy src && pytest
```

Tests are fully mocked (no network). MIT licensed.
