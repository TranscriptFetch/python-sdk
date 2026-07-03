"""Auto-paginate through a channel's videos (follows next_cursor for you)."""

from transcriptfetch import TranscriptFetch

with TranscriptFetch() as tf:
    for i, video in enumerate(tf.transcripts.iter_channel("@lexfridman", limit=10)):
        print(video.video_id, "-", video.title)
        if i >= 24:  # stop after 25
            break
