import os
import random
from moviepy.editor import AudioFileClip, CompositeAudioClip, afx

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SHORTS_MUSIC = os.path.join(BASE, "assets", "shorts_music")
SHORTS_SFX   = os.path.join(BASE, "assets", "shorts_sfx")


def build_shorts_audio(voice_clip):
    """
    Professional shorts audio mix:
    - voice dominant
    - background music low + looped
    - minimal sfx accents
    """

    layers = [voice_clip.volumex(1.0)]

    voice_dur = voice_clip.duration

    # 🎵 BACKGROUND MUSIC (OPTIONAL BUT RECOMMENDED)
    music_files = [
        f for f in os.listdir(SHORTS_MUSIC)
        if f.lower().endswith((".mp3", ".wav"))
    ]

    if music_files:
        music_path = os.path.join(
            SHORTS_MUSIC,
            random.choice(music_files)
        )

        music = (
            AudioFileClip(music_path)
            .audio_loop(duration=voice_dur)
            .volumex(0.12)   # 🔑 low volume (monetization safe)
        )

        layers.append(music)

    # 🔊 SFX (VERY CONTROLLED)
    sfx_files = [
        f for f in os.listdir(SHORTS_SFX)
        if f.lower().endswith((".mp3", ".wav"))
    ]

    if sfx_files:
        sfx_hits = random.randint(2, 4)

        for _ in range(sfx_hits):
            sfx_path = os.path.join(
                SHORTS_SFX,
                random.choice(sfx_files)
            )

            sfx = (
                AudioFileClip(sfx_path)
                .volumex(0.35)
            )

            max_start = max(0, voice_dur - sfx.duration - 0.2)
            start_t = random.uniform(0.3, max_start)

            layers.append(sfx.set_start(start_t))

    return CompositeAudioClip(layers)
