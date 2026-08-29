import os
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeAudioClip,
    vfx
)

BASE = r"D:\video_ai_editor"

CLIPS_DIR = os.path.join(BASE, "inputs", "clips")
VOICES_DIR = os.path.join(BASE, "inputs", "voices")
MUSIC_DIR = os.path.join(BASE, "assets", "music")
SFX_DIR = os.path.join(BASE, "assets", "sfx")
FINAL_DIR = os.path.join(BASE, "engine", "final")

clips_files = [f for f in os.listdir(CLIPS_DIR) if f.endswith(".mp4")]
music_file = os.listdir(MUSIC_DIR)[0]
sfx_file = os.listdir(SFX_DIR)[0]

for voice_name in os.listdir(VOICES_DIR):
    if not voice_name.lower().endswith((".mp3", ".wav")):
        continue

    print("\n🎧 Processing:", voice_name)

    voice = AudioFileClip(os.path.join(VOICES_DIR, voice_name))
    duration = voice.duration
    MODE = "SHORT" if duration <= 90 else "LONG"

    clips = []
    for f in clips_files:
        c = VideoFileClip(os.path.join(CLIPS_DIR, f)).resize((1920,1080))

        if MODE == "SHORT":
            c = c.fx(vfx.speedx, 1.2).fx(vfx.fadein, 0.3)
        else:
            c = c.fx(vfx.fadein, 0.6).fx(vfx.fadeout, 0.6)

        clips.append(c)

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_duration(duration)

    bg = AudioFileClip(os.path.join(MUSIC_DIR, music_file)).volumex(0.12)
    sfx = AudioFileClip(os.path.join(SFX_DIR, sfx_file)).volumex(0.3)

    audio = CompositeAudioClip([
        voice,
        bg.set_duration(duration),
        sfx.set_start(1)
    ])

    video = video.set_audio(audio)

    out_name = voice_name.split(".")[0] + f"_{MODE}.mp4"
    out_path = os.path.join(FINAL_DIR, out_name)

    video.write_videofile(
        out_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="veryfast"
    )

    print("✅ DONE:", out_name)

print("\n🎉 ALL VOICES RENDERED")
