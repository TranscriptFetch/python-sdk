"""Shared fixture data for the test suite."""

from __future__ import annotations

from typing import Any, Optional

BASE = "https://transcriptfetch.com"

VIDEO_ENV: dict[str, Any] = {
    "ok": True,
    "request_id": "req_video",
    "data": {
        "kind": "transcript",
        "video_id": "abc",
        "title": "Example",
        "text": "hello world",
        "segments": [{"start": 0, "duration": 1.5, "text": "hi"}],
    },
    "usage": {"credits_spent": 1, "balance": 99, "bytes": 100},
}

BATCH_ENV: dict[str, Any] = {
    "ok": True,
    "request_id": "req_batch",
    "data": {
        "kind": "transcript_batch",
        "results": [
            # The API no longer includes a "cached" key on batch results.
            {"video_id": "a", "outcome": "ok", "text": "one", "bytes": 10},
            {
                "video_id": "b",
                "outcome": "no_transcript",
                "segments": None,
                "bytes": 0,
            },
            # mode="auto" (default): a captionless entry escalates to audio.
            {
                "video_id": "c",
                "outcome": "processing",
                "status": "processing",
                "job_id": "asr_batch_1",
                "bytes": 0,
            },
        ],
    },
    "usage": {"credits_spent": 1, "balance": 98, "bytes": 10},
}

ME_ENV: dict[str, Any] = {
    "ok": True,
    "request_id": "req_me",
    "data": {"kind": "me", "user_id": "user_1", "credits": 250},
    "usage": {"credits_spent": 0, "balance": 250, "bytes": 0},
}

# A 202 from /transcripts/video: no captions, so audio transcription started.
JOB_ACCEPTED_ENV: dict[str, Any] = {
    "ok": True,
    "request_id": "req_job",
    "status": "processing",
    "job_id": "asr_1",
    "poll_url": "/api/v1/transcripts/jobs/asr_1",
    "data": {"kind": "transcript_job", "video_id": "abc", "platform": "tiktok"},
}

JOB_PROCESSING_ENV: dict[str, Any] = {
    "ok": True,
    "request_id": "req_job",
    "status": "processing",
    "job_id": "asr_1",
    "data": None,
}

JOB_DONE_ENV: dict[str, Any] = {
    "ok": True,
    "request_id": "req_job",
    "status": "completed",
    "job_id": "asr_1",
    "data": {
        "kind": "transcript",
        "video_id": "abc",
        "title": "Example",
        "text": "hello world",
        "segments": [{"start": 0, "duration": 1.5, "text": "hi"}],
    },
    "usage": {"credits_spent": 1, "balance": 96, "bytes": 100},
}

# A podcast link: 202 with the resolved show/episode, then the finished job.
# Podcast audio never has captions, so this is the only path a podcast takes.
PODCAST_ACCEPTED_ENV: dict[str, Any] = {
    "ok": True,
    "request_id": "req_pod",
    "status": "processing",
    "job_id": "asr_2",
    "poll_url": "/api/v1/transcripts/jobs/asr_2",
    "data": {
        "kind": "transcript_job",
        "video_id": "https://feeds.example.com/show.xml",
        "platform": "podcast",
        "podcast": {
            "show": "The Example Show",
            "episode": "Ep 12: Widgets",
            "published_at": "2026-07-01T00:00:00.000Z",
            "feed_url": "https://feeds.example.com/show.xml",
            "audio_url": "https://cdn.example.com/ep12.mp3",
            "resolved_via": "rss",
        },
    },
}

PODCAST_DONE_ENV: dict[str, Any] = {
    "ok": True,
    "request_id": "req_pod",
    "status": "completed",
    "job_id": "asr_2",
    "data": {
        "kind": "transcript",
        "video_id": "https://feeds.example.com/show.xml",
        "platform": "podcast",
        "title": "Ep 12: Widgets",
        "podcast": {"show": "The Example Show", "episode": "Ep 12: Widgets"},
        "text": "welcome back",
        "segments": [{"start": 0, "duration": 2.0, "text": "welcome back"}],
    },
    "usage": {"credits_spent": 1, "balance": 95, "bytes": 200},
}

HEALTH: dict[str, Any] = {
    "status": "ok",
    "service": "transcriptfetch-api",
    "version": "1.0.0",
    "time": "2026-06-16T00:00:00.000Z",
}


def video_list(videos: list[dict[str, Any]], next_cursor: Optional[str]) -> dict[str, Any]:
    return {
        "ok": True,
        "request_id": "req_list",
        "data": {
            "kind": "video_list",
            "source": "channel_videos",
            "videos": videos,
            "next_cursor": next_cursor,
        },
        "usage": {"credits_spent": 1, "balance": 97, "bytes": 0},
    }


def error_env(
    code: str, message: str = "err", issues: Optional[list[Any]] = None
) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if issues is not None:
        err["issues"] = issues
    return {"ok": False, "request_id": "req_err", "error": err}
