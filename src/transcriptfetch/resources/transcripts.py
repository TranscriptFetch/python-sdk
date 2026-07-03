"""The ``transcripts`` resource: video / channel / playlist / search / batch,
plus auto-paginating iterators. Sync (:class:`Transcripts`) and async
(:class:`AsyncTranscripts`) variants share the parsing helpers below.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterable, Iterator, Optional, Protocol

from ..models import BatchResponse, Transcript, Usage, VideoList

# ── Paths ────────────────────────────────────────────────────────────────────
_VIDEO = "/api/v1/transcripts/video"
_CHANNEL = "/api/v1/transcripts/channel"
_PLAYLIST = "/api/v1/transcripts/playlist"
_SEARCH = "/api/v1/transcripts/search"
_BATCH = "/api/v1/transcripts/batch"


# ── Requester protocols (avoid importing the client → no circular import) ─────
class _SyncRequester(Protocol):
    def _request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[dict[str, Any]] = ...,
        idempotency_key: Optional[str] = ...,
        auth: bool = ...,
        idempotent: bool = ...,
    ) -> dict[str, Any]: ...


class _AsyncRequester(Protocol):
    async def _request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[dict[str, Any]] = ...,
        idempotency_key: Optional[str] = ...,
        auth: bool = ...,
        idempotent: bool = ...,
    ) -> dict[str, Any]: ...


# ── Shared parsing ────────────────────────────────────────────────────────────
def _usage(env: dict[str, Any]) -> Optional[Usage]:
    raw = env.get("usage")
    return Usage.model_validate(raw) if isinstance(raw, dict) else None


def _parse_transcript(env: dict[str, Any]) -> Transcript:
    model = Transcript.model_validate(env.get("data", {}))
    model.usage = _usage(env)
    return model


def _parse_videolist(env: dict[str, Any]) -> VideoList:
    model = VideoList.model_validate(env.get("data", {}))
    model.usage = _usage(env)
    return model


def _parse_batch(env: dict[str, Any]) -> BatchResponse:
    model = BatchResponse.model_validate(env.get("data", {}))
    model.usage = _usage(env)
    return model


def _list_body(
    key: str, value: str, limit: Optional[int], cursor: Optional[str]
) -> dict[str, Any]:
    body: dict[str, Any] = {key: value}
    if limit is not None:
        body["limit"] = limit
    if cursor is not None:
        body["cursor"] = cursor
    return body


# ── Sync ──────────────────────────────────────────────────────────────────────
class Transcripts:
    def __init__(self, client: _SyncRequester) -> None:
        self._c = client

    def video(self, video: str, *, idempotency_key: Optional[str] = None) -> Transcript:
        """Fetch a single video's transcript (text + timestamped segments)."""
        env = self._c._request(
            "POST", _VIDEO, body={"video": video}, idempotent=True, idempotency_key=idempotency_key
        )
        return _parse_transcript(env)

    def channel(
        self,
        channel: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> VideoList:
        """List a channel's videos (metadata only), one page."""
        env = self._c._request(
            "POST", _CHANNEL, body=_list_body("channel", channel, limit, cursor),
            idempotent=True, idempotency_key=idempotency_key,
        )
        return _parse_videolist(env)

    def playlist(
        self,
        playlist: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> VideoList:
        """List a playlist's videos (metadata only), one page."""
        env = self._c._request(
            "POST", _PLAYLIST, body=_list_body("playlist", playlist, limit, cursor),
            idempotent=True, idempotency_key=idempotency_key,
        )
        return _parse_videolist(env)

    def search(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> VideoList:
        """Search YouTube and return matching videos (metadata only), one page."""
        env = self._c._request(
            "POST", _SEARCH, body=_list_body("query", query, limit, cursor),
            idempotent=True, idempotency_key=idempotency_key,
        )
        return _parse_videolist(env)

    def batch(
        self, video_ids: Iterable[str], *, idempotency_key: Optional[str] = None
    ) -> BatchResponse:
        """Fetch up to 50 transcripts in one call."""
        env = self._c._request(
            "POST", _BATCH, body={"videoIds": list(video_ids)},
            idempotent=True, idempotency_key=idempotency_key,
        )
        return _parse_batch(env)

    # Auto-paginating iterators ------------------------------------------------
    def iter_channel(self, channel: str, *, limit: Optional[int] = None) -> Iterator[Any]:
        return self._iter(self.channel, channel, limit)

    def iter_playlist(self, playlist: str, *, limit: Optional[int] = None) -> Iterator[Any]:
        return self._iter(self.playlist, playlist, limit)

    def iter_search(self, query: str, *, limit: Optional[int] = None) -> Iterator[Any]:
        return self._iter(self.search, query, limit)

    def _iter(self, method: Any, value: str, limit: Optional[int]) -> Iterator[Any]:
        cursor: Optional[str] = None
        while True:
            page: VideoList = method(value, limit=limit, cursor=cursor)
            yield from page.videos
            if not page.next_cursor:
                return
            cursor = page.next_cursor


# ── Async ─────────────────────────────────────────────────────────────────────
class AsyncTranscripts:
    def __init__(self, client: _AsyncRequester) -> None:
        self._c = client

    async def video(self, video: str, *, idempotency_key: Optional[str] = None) -> Transcript:
        env = await self._c._request(
            "POST", _VIDEO, body={"video": video}, idempotent=True, idempotency_key=idempotency_key
        )
        return _parse_transcript(env)

    async def channel(
        self,
        channel: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> VideoList:
        env = await self._c._request(
            "POST", _CHANNEL, body=_list_body("channel", channel, limit, cursor),
            idempotent=True, idempotency_key=idempotency_key,
        )
        return _parse_videolist(env)

    async def playlist(
        self,
        playlist: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> VideoList:
        env = await self._c._request(
            "POST", _PLAYLIST, body=_list_body("playlist", playlist, limit, cursor),
            idempotent=True, idempotency_key=idempotency_key,
        )
        return _parse_videolist(env)

    async def search(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> VideoList:
        env = await self._c._request(
            "POST", _SEARCH, body=_list_body("query", query, limit, cursor),
            idempotent=True, idempotency_key=idempotency_key,
        )
        return _parse_videolist(env)

    async def batch(
        self, video_ids: Iterable[str], *, idempotency_key: Optional[str] = None
    ) -> BatchResponse:
        env = await self._c._request(
            "POST", _BATCH, body={"videoIds": list(video_ids)},
            idempotent=True, idempotency_key=idempotency_key,
        )
        return _parse_batch(env)

    async def iter_channel(
        self, channel: str, *, limit: Optional[int] = None
    ) -> AsyncIterator[Any]:
        async for v in self._iter(self.channel, channel, limit):
            yield v

    async def iter_playlist(
        self, playlist: str, *, limit: Optional[int] = None
    ) -> AsyncIterator[Any]:
        async for v in self._iter(self.playlist, playlist, limit):
            yield v

    async def iter_search(self, query: str, *, limit: Optional[int] = None) -> AsyncIterator[Any]:
        async for v in self._iter(self.search, query, limit):
            yield v

    async def _iter(self, method: Any, value: str, limit: Optional[int]) -> AsyncIterator[Any]:
        cursor: Optional[str] = None
        while True:
            page: VideoList = await method(value, limit=limit, cursor=cursor)
            for v in page.videos:
                yield v
            if not page.next_cursor:
                return
            cursor = page.next_cursor
