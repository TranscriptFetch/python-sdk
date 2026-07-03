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
