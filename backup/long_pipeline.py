

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
