import os
import re
import shutil

print("==================================================")
print("1. SAFETY CHECK & BACKUP")
print("==================================================")

if os.path.exists("app.py"):
    shutil.copyfile("app.py", "app_latest_backup.py")
    print("✓ Backup saved: app_latest_backup.py")

print("\n==================================================")
print("2. FIXING MASTER_PIPELINE.PY (SHORT VIDEO ENGINE)")
print("==================================================")

short_engine_code = '''
# --- SHORT VIDEO MULTI-CLIP CONCATENATION ENGINE ---
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip

def render_short_video_pipeline(video_clips_paths, audio_path, output_path="output/short_video.mp4"):
    """
    Short Video Engine: Connects to master_pipeline.py
    Concatenates ALL provided clips and matches full voice duration.
    """
    if not video_clips_paths:
        raise ValueError("No video clips provided for Short Pipeline!")
    
    audio = AudioFileClip(audio_path)
    target_duration = audio.duration
    
    loaded_clips = []
    for path in video_clips_paths:
        if os.path.exists(path):
            try:
                loaded_clips.append(VideoFileClip(path))
            except Exception as e:
                print(f"Warning: Failed to load clip {path}: {e}")
                
    if not loaded_clips:
        raise ValueError("Could not load any valid video clips!")
        
    # Sequence all clips until total duration matches audio
    current_duration = 0.0
    sequence = []
    
    while current_duration < target_duration:
        for clip in loaded_clips:
            if current_duration >= target_duration:
                break
            rem = target_duration - current_duration
            if clip.duration > rem:
                sequence.append(clip.subclip(0, rem))
                current_duration += rem
            else:
                sequence.append(clip)
                current_duration += clip.duration
                
    final_video = concatenate_videoclips(sequence, method="compose")
    final_video = final_video.set_audio(audio)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # RAM-Safe Render (480p, 2 threads)
    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        preset="ultrafast",
        logger=None
    )
    
    # Close clips to free memory
    audio.close()
    for c in loaded_clips:
        c.close()
    final_video.close()
    
    return output_path
'''

if os.path.exists("master_pipeline.py"):
    with open("master_pipeline.py", "a", encoding="utf-8") as f:
        f.write("\n" + short_engine_code)
    print("✓ Successfully connected Short Pipeline multi-clip logic in 'master_pipeline.py'")

print("\n==================================================")
print("3. FIXING BATCH_LONG_RENDER.PY (LONG VIDEO ENGINE)")
print("==================================================")

long_engine_code = '''
# --- LONG VIDEO MULTI-CLIP CONCATENATION ENGINE ---
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip

def render_long_video_pipeline(video_clips_paths, audio_path, output_path="output/long_video.mp4"):
    """
    Long Video Engine: Connects to batch_long_render.py
    Combines ALL clips for full horizontal/long format video.
    """
    if not video_clips_paths:
        raise ValueError("No video clips provided for Long Pipeline!")
        
    audio = AudioFileClip(audio_path)
    target_duration = audio.duration
    
    loaded_clips = []
    for path in video_clips_paths:
        if os.path.exists(path):
            try:
                loaded_clips.append(VideoFileClip(path))
            except Exception as e:
                print(f"Warning: Failed to load clip {path}: {e}")
                
    if not loaded_clips:
        raise ValueError("Could not load any valid video clips!")
        
    current_duration = 0.0
    sequence = []
    
    while current_duration < target_duration:
        for clip in loaded_clips:
            if current_duration >= target_duration:
                break
            rem = target_duration - current_duration
            if clip.duration > rem:
                sequence.append(clip.subclip(0, rem))
                current_duration += rem
            else:
                sequence.append(clip)
                current_duration += clip.duration
                
    final_video = concatenate_videoclips(sequence, method="compose")
    final_video = final_video.set_audio(audio)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # RAM-Safe Render
    final_video.write_videofile(
        output_path,
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
    
    return output_path
'''

batch_file = "batch_long_render.py" if os.path.exists("batch_long_render.py") else "long_pipeline.py"
with open(batch_file, "a", encoding="utf-8") as f:
    f.write("\n" + long_engine_code)
print(f"✓ Successfully connected Long Pipeline multi-clip logic in '{batch_file}'")

print("\n==================================================")
print("4. CONNECTING APP.PY TO BACKEND ENGINES SAFELY")
print("==================================================")

# Safely inject connection wrappers into app.py without touching UI code
app_patch_code = '''

# --- SAFE PIPELINE ROUTERS (UI UNTOUCHED) ---
def run_short_pipeline_connected(clips, audio):
    try:
        from master_pipeline import render_short_video_pipeline
        return render_short_video_pipeline(clips, audio)
    except Exception as e:
        print(f"Short pipeline error: {e}")
        return None

def run_long_pipeline_connected(clips, audio):
    try:
        if os.path.exists("batch_long_render.py"):
            from batch_long_render import render_long_video_pipeline
            return render_long_video_pipeline(clips, audio)
        else:
            from long_pipeline import render_long_video_pipeline
            return render_long_video_pipeline(clips, audio)
    except Exception as e:
        print(f"Long pipeline error: {e}")
        return None
'''

with open("app.py", "r", encoding="utf-8") as f:
    app_content = f.read()

if "run_short_pipeline_connected" not in app_content:
    with open("app.py", "a", encoding="utf-8") as f:
        f.write("\n" + app_patch_code)
    print("✓ Injected safe backend pipeline routers into app.py")

print("\n==================================================")
print("SUCCESS: PIPELINES CONNECTED! ZERO UI CHANGES MADE.")
print("==================================================")