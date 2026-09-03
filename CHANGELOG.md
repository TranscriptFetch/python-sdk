# Changelog

All notable changes to this project are documented here. This project adheres to
[Semantic Versioning](https://semver.org).

## [2.0.0] - 2026-09-03

Targets API v2 (`/api/v2`). v1 is deprecated server-side with a twelve-month
window, so 1.x keeps working until 2027-09-03; upgrade before then.

### Breaking

- Every request goes to `/api/v2/...`.
- `APIError` gains `number` (stable integer code; the thousands digit is the
  family, 5xxx = retry), `docs`, `retry_with`, `details`, and a `retryable`
  property. New subclasses: `NotFoundError` (404), `BatchTooLargeError` (400,
  `details["max"]`), `UnprocessableInputError` (422, the whole 3xxx/4xxx
  family: unsupported platform, no captions, private, live, and so on;
  `retry_with` is set when a different request would work, e.g.
  `{"mode": "audio"}`).
- `BatchResult`: `outcome` is exactly `"ok" | "processing" | "error"`; the
  deprecated `cached` and `status` fields are gone; failed entries carry
  `error` (an `ApiErrorBlock`, the same shape a request-level error raises);
  `source` and `poll_url` added.
- `Transcript.error` (an `ApiErrorBlock`) is set on a failed job polled via
  `transcripts.job()`.

### Added

- `Transcript.source`: `"captions"` or `"audio"`, where the words came from.
- `ApiErrorBlock` model.

## [1.0.2] - 2026-08-28

Batch grew audio fallback on the API side; this release types it.

- `transcripts.batch()` (sync + async) gains `mode="auto" | "captions"`.
  `"auto"` (the API default) transcribes captionless entries from audio: those
  come back with `outcome == "processing"` and a `job_id`, cost nothing on that
  call, and are charged on delivery at the audio rate — re-send the same batch
  later, or poll the job via `transcripts.job()`. `"captions"` keeps the old
  behaviour (captionless entries fail as `no_transcript`). `"audio"` is not
  accepted on batch.
- `BatchResult` gains `job_id` and `status` for those processing entries.
- Deprecated: `BatchResult.cached`. The API no longer reports cache hits on
  batch results (the key is omitted entirely), so the field is now
  `Optional[bool]` defaulting to `None` instead of a silently-false `bool`.
  Kept for import/attribute compatibility within 1.x; do not branch on it.
- `Segment` gains optional `speaker` (int): best-effort diarization label on
  podcast transcriptions — ids are voice-separation hints, not named
  identification, and non-podcast sources never carry them.
- Error mapping: the wire code `upstream_error` (503, upstream platform
  blocked) now maps to `UpstreamUnavailableError` by code as well as by
  status. Behaviour is unchanged — 503 already mapped and retried — but the
  docstring no longer claims 502 only. Per-key rate limits remain 429
  (`RateLimitError`); upstream blocks are never 429.

## [1.0.0] - 2026-08-05

First stable release. The published docs promise the SDKs follow semver, and a
0.x version explicitly reserves the right to break anything, so the surface is
declared stable at 1.0.0 rather than contradicting that.

- Full API coverage: added `me()` (validate the key + read the balance, free)
  and `transcripts.job()` (poll an audio-transcription job), on both clients.
- `transcripts.video` / `batch` are now documented as accepting any supported
  source: YouTube, TikTok, Instagram, direct media file URLs, and podcast links
  (a Spotify or Apple Podcasts episode URL, or an RSS feed URL, resolved to that
  episode's audio automatically). `channel`, `playlist` and `search` remain
  YouTube-only concepts. No behavior change; the clients always passed the input
  through untouched.
- New `Podcast` model on `Transcript.podcast`, carrying the show and episode a
  podcast link resolved to, plus `Transcript.platform`.
- Fixed: a 202 (no captions, so audio transcription started) raised a validation
  error because `Transcript.kind` was pinned to `"transcript"`. It now returns a
  `Transcript` with `status="processing"` and a `job_id` to poll.
- New `Account` model; `Transcript` gains `status`, `job_id` and `poll_url`.

## [0.1.0] - Unreleased

Initial release.

- Sync `TranscriptFetch` and async `AsyncTranscriptFetch` clients (httpx).
- `transcripts.video / channel / playlist / search / batch` + `health()`.
- Auto-paginating `iter_channel / iter_playlist / iter_search`.
- Typed Pydantic v2 models (`Transcript`, `VideoList`, `Video`, `Segment`, `BatchResponse`, `Usage`).
- Typed exception hierarchy mapped from the API's canonical error codes.
- Automatic retries with backoff (429 + 5xx) and auto Idempotency-Key.
