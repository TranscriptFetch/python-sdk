# Changelog

All notable changes to this project are documented here. This project adheres to
[Semantic Versioning](https://semver.org).

## [1.0.0] - 2026-08-05

First stable release. The published docs promise the SDKs follow semver, and a
0.x version explicitly reserves the right to break anything, so the surface is
declared stable at 1.0.0 rather than contradicting that.

- Full API coverage: added `me()` (validate the key + read the balance, free)
  and `transcripts.job()` (poll an audio-transcription job), on both clients.
- `transcripts.video` / `batch` are now documented as accepting any supported
  source: YouTube, TikTok, Instagram, and direct media file URLs. `channel`,
  `playlist` and `search` remain YouTube-only concepts. No behavior change; the
  clients always passed the input through untouched.
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
