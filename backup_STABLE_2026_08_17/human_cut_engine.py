import random
from moviepy.editor import concatenate_videoclips

def build_human_timeline(clips, words, total_duration):
    timeline = []
    t = 0

    while t < total_duration:
        c = random.choice(clips)

        cut = random.uniform(1.6, 2.6)

        if cut > c.duration:
            cut = c.duration

        clip = c.subclip(0, cut)
        timeline.append(clip)

        t += cut

    video = concatenate_videoclips(timeline, method="chain")
    return video.subclip(0, total_duration)
