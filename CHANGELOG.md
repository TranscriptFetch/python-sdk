# Changelog

All notable changes to this project are documented here. This project adheres to
[Semantic Versioning](https://semver.org).

## [0.1.0] - Unreleased

Initial release.

- Sync `TranscriptFetch` and async `AsyncTranscriptFetch` clients (httpx).
- `transcripts.video / channel / playlist / search / batch` + `health()`.
- Auto-paginating `iter_channel / iter_playlist / iter_search`.
- Typed Pydantic v2 models (`Transcript`, `VideoList`, `Video`, `Segment`, `BatchResponse`, `Usage`).
- Typed exception hierarchy mapped from the API's canonical error codes.
- Automatic retries with backoff (429 + 5xx) and auto Idempotency-Key.
