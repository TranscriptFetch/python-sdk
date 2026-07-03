"""Fetch a single transcript.

Run with your key set:  TRANSCRIPTFETCH_API_KEY=tf_live_... python examples/quickstart.py
"""

from transcriptfetch import TranscriptFetch

with TranscriptFetch() as tf:  # reads TRANSCRIPTFETCH_API_KEY
    t = tf.transcripts.video("https://youtu.be/aircAruvnKk")
    print("title:", t.title)
    print("text:", (t.text or "(no transcript)")[:500])
    print("segments:", len(t.segments))
    if t.usage:
        print(f"credits spent: {t.usage.credits_spent} · balance: {t.usage.balance}")
