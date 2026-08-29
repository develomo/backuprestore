import os
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeAudioClip,
    vfx
)

BASE = r"D:\video_ai_editor"

CLIPS = os.path.join(BASE, "inputs", "clips")
VOICES = os.path.join(BASE, "inputs", "voices")
MUSIC = os.path.join(BASE, "assets", "music")
SFX = os.path.join(BASE, "assets", "sfx")
FINAL = os.path.join(BASE, "engine", "final")

# ---------- VOICE ----------
voice_file = os.listdir(VOICES)[0]
voice = AudioFileClip(os.path.join(VOICES, voice_file))
duration = voice.duration

MODE = "SHORT" if duration <= 90 else "LONG"
print("🎬 MODE:", MODE)

# ---------- CLIPS ----------
clips = []
for f in sorted(os.listdir(CLIPS)):
    if f.endswith(".mp4"):
        clip = VideoFileClip(os.path.join(CLIPS, f)).resize((1920,1080))

        if MODE == "SHORT":
            clip = clip.fx(vfx.speedx, 1.15).fx(vfx.fadein, 0.3)
        else:
            clip = clip.fx(vfx.fadein, 0.6).fx(vfx.fadeout, 0.6)

        clips.append(clip)

video = concatenate_videoclips(clips, method="compose")
video = video.set_duration(duration)

# ---------- AUDIO ----------
audios = [voice]

# background music
bg_files = os.listdir(MUSIC)
if bg_files:
    bg = AudioFileClip(os.path.join(MUSIC, bg_files[0])).volumex(0.12)
    audios.append(bg.set_duration(duration))

# sfx
sfx_files = os.listdir(SFX)
if sfx_files:
    sfx = AudioFileClip(os.path.join(SFX, sfx_files[0])).volumex(0.3)
    audios.append(sfx.set_start(1))

final_audio = CompositeAudioClip(audios)
video = video.set_audio(final_audio)

# ---------- EXPORT ----------
out = os.path.join(FINAL, f"FINAL_{MODE}.mp4")

video.write_videofile(
    out,
    fps=30,
    codec="libx264",
    audio_codec="aac",
    preset="veryfast"
)

print("✅ VIDEO READY:", out)
