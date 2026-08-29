import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

BASE = r"D:\video_ai_editor"

CLIPS_DIR = os.path.join(BASE, "inputs", "clips")
VOICE_DIR = os.path.join(BASE, "inputs", "voices")
OUT_DIR = os.path.join(BASE, "engine", "final")

os.makedirs(OUT_DIR, exist_ok=True)

def make_video():
    voice_file = os.listdir(VOICE_DIR)[0]
    voice = AudioFileClip(os.path.join(VOICE_DIR, voice_file))
    voice_duration = voice.duration

    clips = []
    clip_files = sorted(os.listdir(CLIPS_DIR))

    # decide pacing
    if voice_duration <= 60:
        per_clip = 1.0   # shorts
        mode = "SHORT"
    else:
        per_clip = 2.5   # long
        mode = "LONG"

    current_time = 0

    for f in clip_files:
        if current_time >= voice_duration:
            break

        clip = VideoFileClip(os.path.join(CLIPS_DIR, f))

        clip = clip.subclip(0, min(per_clip, clip.duration))
        clip = clip.resize(1.05)  # light zoom (MrBeast style)

        clips.append(clip)
        current_time += clip.duration

    final = concatenate_videoclips(clips, method="compose")
    final = final.set_audio(voice)
    final = final.subclip(0, voice_duration)

    out = os.path.join(
        OUT_DIR,
        voice_file.replace(".mp3", "") + f"_{mode}_PRO.mp4"
    )

    final.write_videofile(
        out,
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

    print("✅ PROFESSIONAL VIDEO READY:", out)

if __name__ == "__main__":
    make_video()
