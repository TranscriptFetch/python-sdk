"""Fetch a source that may have no captions, then poll until it is transcribed.

Any supported input works here: a YouTube, TikTok or Instagram URL, or a direct
media file URL. When captions exist the first call already returns the text;
when they do not, the API transcribes the audio and hands back a job to poll.
Polling is free, so the loop below costs at most the one credit on delivery.
"""

import time

from transcriptfetch import TranscriptFetch

URL = "https://www.tiktok.com/@nasa/video/7137723462233555205"

with TranscriptFetch() as tf:  # reads TRANSCRIPTFETCH_API_KEY
    t = tf.transcripts.video(URL)

    while t.status == "processing" and t.job_id:
        print("transcribing…", t.job_id)
        time.sleep(3)
        t = tf.transcripts.job(t.job_id)

    print("title:", t.title)
    print("text:", (t.text or "(no transcript)")[:500])
