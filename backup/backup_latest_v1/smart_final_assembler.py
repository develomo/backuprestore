import os
import random
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip
)
from moviepy.video.fx.all import crop, resize, colorx, lum_contrast
from voice_duration import get_voice_duration
from transitions import apply_transitions
from preset_engine import get_preset

BASE = r"D:\video_ai_editor"

CLIPS_DIR = os.path.join(BASE, "inputs", "clips")
VOICES_DIR = os.path.join(BASE, "inputs", "voices")
MUSIC_DIR = os.path.join(BASE, "assets", "music")
FINAL_DIR = os.path.join(BASE, "engine", "final")

os.makedirs(FINAL_DIR, exist_ok=True)

def assemble(voice_file):
    voice_path = os.path.join(VOICES_DIR, voice_file)
    voice_duration = get_voice_duration(voice_path)

    MODE = "SHORT" if voice_duration <= 60 else "LONG"
    preset = get_preset(MODE)

    # ---------------- CLIPS ----------------
    clips = []
    used = 0

    for f in os.listdir(CLIPS_DIR):
        if not f.lower().endswith(".mp4"):
            continue

        clip = VideoFileClip(os.path.join(CLIPS_DIR, f))
        cut = min(
            clip.duration,
            random.uniform(preset["min_clip"], preset["max_clip"])
        )

        clip = clip.subclip(0, cut)
        used += cut

        # color grading
        clip = clip.fx(colorx, preset["color"])
        clip = clip.fx(lum_contrast, 0, preset["contrast"])

        # shorts crop
        if MODE == "SHORT":
            clip = resize(clip, height=1920)
            clip = crop(
                clip,
                x_center=clip.w / 2,
                y_center=clip.h / 2,
                width=1080,
                height=1920
            )

        clips.append(clip)

        if used >= voice_duration:
            break

    video = apply_transitions(clips)
    video = video.set_duration(voice_duration)

    # ---------------- AUDIO ----------------
    voice = AudioFileClip(voice_path)

    music_file = os.listdir(MUSIC_DIR)[0]
    music = AudioFileClip(os.path.join(MUSIC_DIR, music_file))
    music = music.volumex(preset["music_volume"]).set_duration(voice_duration)

    final_audio = CompositeAudioClip([music, voice])
    video = video.set_audio(final_audio)

    # ---------------- EXPORT ----------------
    out_name = voice_file.split(".")[0] + "_READY.mp4"
    out_path = os.path.join(FINAL_DIR, out_name)

    video.write_videofile(
        out_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="veryfast"
    )

    print("✅ FINAL READY:", out_name)

# -------- RUN ALL --------
for v in os.listdir(VOICES_DIR):
    if v.lower().endswith((".mp3", ".wav")):
        assemble(v)

print("🎉 ALL VIDEOS GENERATED PROPERLY")
