from moviepy.editor import VideoFileClip, concatenate_videoclips
from whisper_engine import get_word_timestamps
from caption_engine import generate_captions
from bg_sound_engine import add_background_music
from sfx_engine import add_sfx
from smart_zoom_engine import apply_smart_zoom
from effects_engine import add_beat_flash
import os

# INPUTS & OUTPUTS
INPUT_VIDEO = "inputs/input.mp4"
OUTPUT_VIDEO = "outputs/final_shorts.mp4"
BG_MUSIC = "assets/music/bg.mp3"
MAX_SHORT_DURATION = 30  # max duration per short in seconds

def run_shorts_pipeline():

    print("🚀 Starting Shorts Pipeline...")

    # Load main video
    video = VideoFileClip(INPUT_VIDEO)

    # Step 1: Extract word timestamps using Whisper
    print("🎙 Extracting voice timestamps...")
    words = get_word_timestamps(video.audio)
    
    # Step 2: Generate segments (example: split every 30s or based on speech)
    segments = []
    start = 0
    for w in words:
        end = w["end"]
        if end - start > MAX_SHORT_DURATION:
            segments.append({"start": start, "end": end})
            start = end
    if start < video.duration:
        segments.append({"start": start, "end": video.duration})

    # Step 3: Create individual shorts
    print(f"✂ Creating {len(segments)} shorts...")
    shorts_clips = []
    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        clip = video.subclip(start, end)

        # Resize & crop for 9:16 vertical format
        clip = clip.resize(height=1920)
        clip = clip.crop(width=1080, height=1920, x_center=clip.w/2, y_center=clip.h/2)

        # Apply Smart Zoom
        clip = apply_smart_zoom(clip)

        # Add Captions
        clip = generate_captions(clip)

        # Add Beat Flash & Effects
        clip = add_beat_flash(clip)

        # Add SFX
        clip = add_sfx(clip)

        shorts_clips.append(clip)

    # Step 4: Concatenate all shorts into one final video
    final_video = concatenate_videoclips(shorts_clips, method="compose")

    # Step 5: Add Background Music
    final_video = add_background_music(final_video, BG_MUSIC)

    # Step 6: Export final shorts video
    print("💾 Exporting final shorts video...")
    final_video.write_videofile(
        OUTPUT_VIDEO,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k"
    )

    print("✅ Shorts Video Ready!")

# Entry Point
if __name__ == "__main__":
    run_shorts_pipeline()
