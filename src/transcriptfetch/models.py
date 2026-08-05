"""Typed response models (Pydantic v2), matching the TranscriptFetch API schemas.

The API mixes snake_case (transcript/list envelopes) and camelCase (video list
items). We normalize everything to snake_case attributes via field aliases, while
still accepting the wire names on input.
"""

from __future__ import annotations

from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Usage(_Model):
    """Credit + byte accounting returned alongside every successful response."""

    credits_spent: int = 0
    balance: Optional[int] = None  # null for unlimited (admin) accounts
    bytes: int = 0


class Segment(_Model):
    """A single timestamped caption cue."""

    start: float = 0.0
    duration: float = 0.0
    text: str = ""


class Transcript(_Model):
    """A single video's transcript, from any supported source.

    Also covers the "not ready yet" case. When a video has no captions the API
    transcribes the audio and answers 202 with ``kind == "transcript_job"``,
    which is why ``kind`` is a plain ``str``: pinning it to a literal would turn
    a 202 into a validation error instead of a pollable job. In that case
    ``text``/``segments`` are empty and ``status``/``job_id`` are set, so pass
    ``job_id`` to ``transcripts.job()`` until ``status == "completed"``.
    """

    kind: str = "transcript"
    video_id: str = ""
    title: Optional[str] = None
    text: Optional[str] = None
    segments: List[Segment] = Field(default_factory=list)
    usage: Optional[Usage] = None
    # Envelope-level fields, lifted onto the model so an async job round-trips
    # as one object (the API returns them beside ``data``, not inside it).
    status: Optional[str] = None  # "processing" | "completed", async jobs only
    job_id: Optional[str] = None
    poll_url: Optional[str] = None

    @field_validator("segments", mode="before")
    @classmethod
    def _null_segments_to_list(cls, v: Any) -> Any:
        return v or []


class Account(_Model):
    """The calling key's account (``kind == "me"``): identity + credit balance."""

    kind: Literal["me"] = "me"
    user_id: str = ""
    credits: Optional[int] = None  # null for unlimited (admin) accounts
    usage: Optional[Usage] = None


class Video(_Model):
    """A video reference from a channel/playlist/search list (metadata only)."""

    video_id: str = Field(alias="videoId")
    title: Optional[str] = None
    thumbnail_url: Optional[str] = Field(default=None, alias="thumbnailUrl")
    duration: Optional[float] = None
    channel: Optional[str] = None


class VideoList(_Model):
    """A paginated list of videos (``kind == "video_list"``)."""

    kind: Literal["video_list"] = "video_list"
    source: str = ""
    videos: List[Video] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    usage: Optional[Usage] = None


class BatchResult(_Model):
    """One video's result inside a batch response."""

    video_id: str = ""
    outcome: Optional[str] = None  # ok | no_transcript | blocked | error | null
    title: Optional[str] = None
    text: Optional[str] = None
    segments: Optional[List[Segment]] = None
    cached: bool = False
    bytes: int = 0


class BatchResponse(_Model):
    """Result of a batch fetch (``kind == "transcript_batch"``)."""

    kind: Literal["transcript_batch"] = "transcript_batch"
    results: List[BatchResult] = Field(default_factory=list)
    usage: Optional[Usage] = None
