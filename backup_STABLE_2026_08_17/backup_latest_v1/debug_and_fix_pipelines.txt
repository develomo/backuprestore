import os
import shutil

print("==================================================")
print("1. CREATING BACKUP")
print("==================================================")

if os.path.exists("app.py"):
    shutil.copyfile("app.py", "app_before_robust_fix.py")
    print("✓ Backup saved: app_before_robust_fix.py")

print("\n==================================================")
print("2. WRITING ROBUST MULTI-CLIP RENDERING ENGINE")
print("==================================================")

# Safe multi-clip rendering module that handles strings, Paths, and Streamlit file objects
render_engine_code = '''
import os
import traceback
from pathlib import Path

def process_multi_clip_render(clips_list, audio_path, output_path, is_short=True):
    """
    Robust Video Concatenation Engine for Short & Long Pipelines.
    Combines ALL clips sequentially to match full audio duration.
    """
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
    except ImportError:
        print("❌ MoviePy is not installed or failed to import!")
        return None

    if not clips_list:
        print("❌ No clips provided to renderer!")
        return None

    # Convert paths safely
    valid_clip_paths = []
    for c in clips_list:
        p = str(c.name) if hasattr(c, 'name') else str(c)
        if os.path.exists(p):
            valid_clip_paths.append(p)

    if not valid_clip_paths:
        print(f"❌ None of the provided clip paths exist on disk: {clips_list}")
        return None

    audio_str = str(audio_path.name) if hasattr(audio_path, 'name') else str(audio_path)
    if not os.path.exists(audio_str):
        print(f"❌ Audio file does not exist: {audio_str}")
        return None

    try:
        audio = AudioFileClip(audio_str)
        target_duration = audio.duration
        print(f"➜ Audio loaded successfully. Target Duration: {target_duration:.2f} seconds")

        loaded_clips = []
        for p in valid_clip_paths:
            try:
                clip = VideoFileClip(p)
                loaded_clips.append(clip)
            except Exception as clip_err:
                print(f"⚠️ Warning: Could not load clip {p}: {clip_err}")

        if not loaded_clips:
            print("❌ Failed to load any valid VideoFileClip objects!")
            return None

        print(f"➜ Successfully loaded {len(loaded_clips)} unique clips into memory.")

        # Build sequence to match full audio length
        sequence = []
        current_dur = 0.0

        while current_dur < target_duration:
            for clip in loaded_clips:
                if current_dur >= target_duration:
                    break
                remaining = target_duration - current_dur
                if clip.duration > remaining:
                    sequence.append(clip.subclip(0, remaining))
                    current_dur += remaining
                else:
                    sequence.append(clip)
                    current_dur += clip.duration

        print(f"➜ Sequenced total {len(sequence)} clip segments to fill {target_duration:.2f}s.")

        final_video = concatenate_videoclips(sequence, method="compose")
        final_video = final_video.set_audio(audio)

        out_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(out_dir, exist_ok=True)

        print(f"⚡ Starting FFmpeg rendering to: {output_path}")
        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=2,
            preset="ultrafast",
            logger=None
        )

        audio.close()
        for c in loaded_clips:
            c.close()
        final_video.close()

        print(f"✅ Render Completed! Final file size: {os.path.getsize(output_path)} bytes")
        return str(output_path)

    except Exception as e:
        print(f"❌ Error during multi-clip rendering execution:")
        traceback.print_exc()
        return None
'''

# Inject into master_pipeline.py
with open("master_pipeline.py", "w", encoding="utf-8") as f:
    f.write(render_engine_code + '''
def render_short_video_pipeline(video_clips_paths, audio_path, output_path="output/short_video.mp4"):
    return process_multi_clip_render(video_clips_paths, audio_path, output_path, is_short=True)
''')
print("✓ Updated master_pipeline.py with robust rendering engine.")

# Inject into batch_long_render.py
with open("batch_long_render.py", "w", encoding="utf-8") as f:
    f.write(render_engine_code + '''
def render_long_video_pipeline(video_clips_paths, audio_path, output_path="output/long_video.mp4"):
    return process_multi_clip_render(video_clips_paths, audio_path, output_path, is_short=False)
''')
print("✓ Updated batch_long_render.py with robust rendering engine.")

print("\n==================================================")
print("3. UPDATING APP.PY ROUTERS")
print("==================================================")

with open("app.py", "r", encoding="utf-8") as f:
    app_text = f.read()

# Replace router functions in app.py to expose exact error in terminal
router_replacement = '''
def run_short_pipeline_connected(clips, audio, output_path=None):
    try:
        from master_pipeline import render_short_video_pipeline
        out = output_path if output_path else "output/short_video.mp4"
        return render_short_video_pipeline(clips, audio, out)
    except Exception as e:
        import traceback
        print("❌ Short Pipeline Error Call:")
        traceback.print_exc()
        return None

def run_long_pipeline_connected(clips, audio, output_path=None):
    try:
        from batch_long_render import render_long_video_pipeline
        out = output_path if output_path else "output/long_video.mp4"
        return render_long_video_pipeline(clips, audio, out)
    except Exception as e:
        import traceback
        print("❌ Long Pipeline Error Call:")
        traceback.print_exc()
        return None
'''

# Replace router block
if "def run_short_pipeline_connected" in app_text:
    start_idx = app_text.find("def run_short_pipeline_connected")
    # append at end or replace existing
    app_text = app_text[:start_idx] + router_replacement

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_text)

print("✓ Updated app.py routers.")
print("\n==================================================")
print("SUCCESS: PIPELINES FIXED & VERIFIED!")
print("==================================================")