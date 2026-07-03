# TranscriptFetch Python SDK

Official, typed Python client for the [TranscriptFetch](https://transcriptfetch.com) API: fetch YouTube transcripts, channels, playlists, and search results as clean, structured data. Sync + async, fully type-hinted.

```bash
pip install transcriptfetch-sdk
```

## Quickstart

```python
from transcriptfetch import TranscriptFetch

# api_key falls back to the TRANSCRIPTFETCH_API_KEY env var
tf = TranscriptFetch(api_key="tf_live_...")

t = tf.transcripts.video("https://youtu.be/aircAruvnKk")
print(t.title)
print(t.text)
for seg in t.segments:
    print(f"[{seg.start:.1f}] {seg.text}")

print("credits left:", t.usage.balance)
```

Get an API key (100 free credits) at <https://transcriptfetch.com/app>. One credit per successful fetch; failed/blocked/no-transcript requests are free.

## Endpoints

```python
tf.transcripts.video(video)                    # single transcript (text + segments)
tf.transcripts.channel(channel, limit=, cursor=)   # a channel's videos (metadata)
tf.transcripts.playlist(playlist, limit=, cursor=) # a playlist's videos
tf.transcripts.search(query, limit=, cursor=)      # search YouTube
tf.transcripts.batch(video_ids)                # up to 50 transcripts in one call
tf.health()                                    # unauthenticated liveness probe
```

`video`/`channel`/`playlist` accept URLs or raw IDs (normalized automatically).

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
