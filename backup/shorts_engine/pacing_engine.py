from moviepy.editor import VideoFileClip
import random

def apply_shorts_pacing(video):
    """
    Human-like pacing for shorts:
    - micro cuts
    - no over-editing
    """

    clips = []
    t = 0
    dur = video.duration

    while t < dur:
        chunk = random.uniform(0.7, 1.1)
        end = min(t + chunk, dur)

        sub = video.subclip(t, end)

        # micro zoom illusion
        if random.random() < 0.4:
            sub = sub.resize(1.03)

        clips.append(sub)
        t = end

    return clips
