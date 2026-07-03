"""Fetch up to 50 transcripts in one call."""

from transcriptfetch import TranscriptFetch

with TranscriptFetch() as tf:
    res = tf.transcripts.batch(["aircAruvnKk", "Tn6-PIqc4UM"])
    for r in res.results:
        print(r.video_id, r.outcome, "-", (r.text or "")[:60])
    if res.usage:
        print("credits spent:", res.usage.credits_spent)
