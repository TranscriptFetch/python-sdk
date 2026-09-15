# TranscriptFetch Python SDK

Official, typed Python client for the [TranscriptFetch](https://transcriptfetch.com) API: fetch transcripts as clean, structured data, plus channel, playlist and search listings across YouTube, TikTok and Instagram. Sync + async, fully type-hinted.

Transcripts come from **YouTube, TikTok, Instagram, or a direct media file URL** (mp3/mp4/wav and friends). Channel and playlist take a URL from any of those platforms and detect it; search is YouTube by default, or any of them via `platform=`.

```bash
pip install transcriptfetch-sdk
```

## Quickstart

```python
from transcriptfetch import TranscriptFetch

# api_key falls back to the TRANSCRIPTFETCH_API_KEY env var
tf = TranscriptFetch(api_key="tf_live_...")

t = tf.transcripts.video("https://youtu.be/aircAruvnKk")   # or a TikTok / Instagram / file URL
print(t.title)
print(t.text)
for seg in t.segments:
    print(f"[{seg.start:.1f}] {seg.text}")

print("credits left:", t.usage.balance)
```

Every transcript carries the same metadata whichever platform served it:
`video_id`, `url`, `platform`, `title`, `channel` (the creator), `duration` in
seconds, `language`, `thumbnail_url` and `source` (`"captions"` or `"audio"`).
A value the API could not determine is `None`, never missing.

Get an API key (50 free credits) at <https://transcriptfetch.com/app>. One credit per successful fetch; failed/blocked/no-transcript requests are free.

## Endpoints

```python
tf.transcripts.video(video)                        # single transcript (text + segments)
tf.transcripts.batch(video_ids, mode=)             # up to 50 transcripts in one call
tf.transcripts.channel(channel, limit=, cursor=)   # a channel's or creator's videos (metadata)
tf.transcripts.playlist(playlist, limit=, cursor=) # a playlist's videos
tf.transcripts.search(query, platform=, limit=, cursor=)  # keyword search, YouTube by default
tf.transcripts.job(job_id)                         # poll an audio-transcription job (free)
tf.me()                                            # validate the key + read the balance (free)
tf.health()                                        # unauthenticated liveness probe
```

`video` and `batch` take a YouTube, TikTok or Instagram URL, a direct media file URL, or a bare YouTube ID. `channel`/`playlist` take a YouTube, TikTok or Instagram URL (or a YouTube `@handle` / `PL…` id) and detect the platform from it. `search` searches YouTube unless you pass `platform`:

```python
page = tf.transcripts.search("lofi hip hop", platform="tiktok", limit=10)
for v in page.videos:
    print(v.title, v.published_at, v.stats.plays if v.stats else None)
    t = tf.transcripts.video(v.url)
```

## Sources without captions

When a source has no captions, the API transcribes its audio and answers with a job instead of a transcript. That comes back as a `Transcript` with `status == "processing"` and a `job_id`; poll it for free until it completes.

```python
import time

t = tf.transcripts.video("https://www.tiktok.com/@user/video/7137723462233555205")
while t.status == "processing":
    time.sleep(3)
    t = tf.transcripts.job(t.job_id)
print(t.text)
```

Batch works the same way by default (`mode="auto"`): entries with no caption track are transcribed from audio, come back with `outcome == "processing"` and a `job_id`, cost nothing on that call, and are charged on delivery at the audio rate. Re-send the same batch once the jobs have had time to finish and the text comes back normally — or poll each `job_id` with `tf.transcripts.job()`. Pass `mode="captions"` to read existing caption tracks only, in which case a captionless video fails as `outcome == "error"` with `error.code == "no_captions"` (and `error.retry_with` naming the audio mode):

```python
res = tf.transcripts.batch(ids)                    # captionless entries -> "processing" + job_id
pending = [r.job_id for r in res.results if r.outcome == "processing"]

res = tf.transcripts.batch(ids, mode="captions")   # captions only, no audio fallback
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

All errors subclass `TranscriptFetchError`. API errors carry `.status`, `.code`, `.number` (the thousands digit is the family; 5xxx means retry), `.message`, `.docs`, `.retry_with` (the request change that would succeed, when there is one), `.details`, `.request_id`, and a `.retryable` property:

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
