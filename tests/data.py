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
            {"video_id": "a", "outcome": "ok", "text": "one", "cached": False, "bytes": 10},
            {
                "video_id": "b",
                "outcome": "no_transcript",
                "segments": None,
                "cached": True,
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
