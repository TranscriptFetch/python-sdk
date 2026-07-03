"""Async usage. TRANSCRIPTFETCH_API_KEY=tf_live_... python examples/async_example.py"""

import asyncio

from transcriptfetch import AsyncTranscriptFetch


async def main() -> None:
    async with AsyncTranscriptFetch() as tf:
        t = await tf.transcripts.video("aircAruvnKk")
        print((t.text or "(no transcript)")[:200])


asyncio.run(main())
