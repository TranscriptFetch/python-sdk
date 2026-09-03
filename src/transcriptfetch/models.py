"""Typed response models (Pydantic v2), matching the TranscriptFetch API schemas.

The API mixes snake_case (transcript/list envelopes) and camelCase (video list
items). We normalize everything to snake_case attributes via field aliases, while
still accepting the wire names on input.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Usage(_Model):
    """Credit + byte accounting returned alongside every successful response."""

    credits_spent: int = 0
    balance: Optional[int] = None  # null for unlimited (admin) accounts
    bytes: int = 0


class Segment(_Model):
    """A single timestamped caption cue.

    ``speaker`` is set only on podcast episodes transcribed from audio, where
    best-effort diarization labels each segment with a small integer (0, 1, …)
    identifying who is talking. The ids are hints from voice separation, not
    named identification, and non-podcast sources never carry them.
    """

    start: float = 0.0
    duration: float = 0.0
    text: str = ""
    speaker: Optional[int] = None


class Podcast(_Model):
    """Show/episode context, present when the input resolved to a podcast.

    Only ``show`` and ``episode`` are dependable. A cached hit on a bare audio
    URL knows its show but not the feed it was resolved from, so the resolution
    fields come back empty there.
    """

    show: Optional[str] = None
    episode: Optional[str] = None
    published_at: Optional[str] = None
    feed_url: Optional[str] = None
    audio_url: Optional[str] = None
    resolved_via: Optional[str] = None


class Transcript(_Model):
    """A single video's transcript, from any supported source.

    Also covers the "not ready yet" case. When a video has no captions the API
    transcribes the audio and answers 202 with ``kind == "transcript_job"``,
    which is why ``kind`` is a plain ``str``: pinning it to a literal would turn
    a 202 into a validation error instead of a pollable job. In that case
    ``text``/``segments`` are empty and ``status``/``job_id`` are set, so pass
    ``job_id`` to ``transcripts.job()`` until ``status == "completed"``.
    Podcasts always take that path, since podcast audio never has captions.
    """

    kind: str = "transcript"
    video_id: str = ""
    platform: Optional[str] = None  # youtube | tiktok | instagram | podcast | file
    title: Optional[str] = None
    source: Optional[str] = None  # "captions" | "audio" (AI transcription); None on a 202
    text: Optional[str] = None
    segments: List[Segment] = Field(default_factory=list)
    podcast: Optional[Podcast] = None  # set only when the input was a podcast
    usage: Optional[Usage] = None
    # Envelope-level fields, lifted onto the model so an async job round-trips
    # as one object (the API returns them beside ``data``, not inside it).
    status: Optional[str] = None  # "processing" | "completed" | "failed", async jobs only
    job_id: Optional[str] = None
    poll_url: Optional[str] = None
    error: Optional["ApiErrorBlock"] = None
    """Why a job failed. Set only when ``status == "failed"``."""

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


class ApiErrorBlock(_Model):
    """The API's error block, as it appears on a failed batch entry or a
    failed job. Request-level failures raise :class:`APIError` with the same
    fields. ``number``'s thousands digit is the family; 5xxx means retry."""

    code: str = ""
    number: Optional[int] = None
    message: str = ""
    docs: Optional[str] = None
    retry_with: Optional[Dict[str, Any]] = None
    """The request change that would succeed, e.g. ``{"mode": "audio"}``."""
    details: Optional[Dict[str, Any]] = None


class BatchResult(_Model):
    """One video's result inside a batch response.

    Exactly three outcomes. ``"ok"`` carries the transcript (``text``,
    ``segments``, ``source``). ``"processing"`` carries the audio-transcription
    job started for a captionless entry (batch ``mode="auto"``): it costs
    nothing on that call and is charged on delivery at the audio rate; either
    re-send the same batch once the jobs have had time to finish or poll
    ``job_id`` via ``transcripts.job()``. ``"error"`` carries the same error
    block a request-level failure raises, in ``error``. Send
    ``mode="captions"`` to have captionless entries fail as ``"error"`` with
    code ``no_captions`` (and ``error.retry_with`` naming the audio mode).
    """

    video_id: str = ""
    outcome: str = "error"  # ok | processing | error
    error: Optional[ApiErrorBlock] = None
    title: Optional[str] = None
    source: Optional[str] = None  # "captions" | "audio" on outcome "ok"
    text: Optional[str] = None
    segments: Optional[List[Segment]] = None
    job_id: Optional[str] = None
    """Set when ``outcome == "processing"``: the audio-transcription job that
    will deliver this entry."""
    poll_url: Optional[str] = None
    bytes: int = 0


class BatchResponse(_Model):
    """Result of a batch fetch (``kind == "transcript_batch"``)."""

    kind: Literal["transcript_batch"] = "transcript_batch"
    results: List[BatchResult] = Field(default_factory=list)
    usage: Optional[Usage] = None
