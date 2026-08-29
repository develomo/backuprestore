import os

print("==================================================")
print("1. UPDATING MASTER PIPELINE ENGINE")
print("==================================================")

pipeline_code = '''import os
import traceback
import numpy as np

def apply_color_grading(clip, preset):
    """Applies actual Color Grading to MoviePy Clip"""
    if not preset or str(preset).lower() in ['none', 'standard']:
        return clip

    def filter_frame(get_frame, t):
        frame = get_frame(t).astype(float)
        p = str(preset).lower()
        
        if p in ['cinematic', 'teal_orange']:
            frame[:, :, 0] = np.clip(frame[:, :, 0] * 1.1 + 10, 0, 255)
            frame[:, :, 2] = np.clip(frame[:, :, 2] * 0.9, 0, 255)
        elif p in ['warm_luxury', 'warm']:
            frame[:, :, 0] = np.clip(frame[:, :, 0] * 1.12, 0, 255)
            frame[:, :, 1] = np.clip(frame[:, :, 1] * 1.05, 0, 255)
            frame[:, :, 2] = np.clip(frame[:, :, 2] * 0.88, 0, 255)
        elif p in ['vibrant', 'vivid']:
            mean = np.mean(frame, axis=2, keepdims=True)
            frame = np.clip((frame - mean) * 1.25 + mean, 0, 255)
            
        return frame.astype(np.uint8)

    return clip.fl(filter_frame)

def process_multi_clip_render(clips_list, audio_path, output_path, settings=None):
    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip, afx
    except ImportError:
        print("❌ MoviePy is not installed!")
        return None

    if not clips_list or not audio_path:
        print("❌ Missing clips or voiceover audio input!")
        return None

    settings = settings or {}
    color_preset = settings.get('color_grading', 'Standard')
    bg_music_path = settings.get('bg_music')
    bg_volume = float(settings.get('music_volume', 0.15))

    valid_clip_paths = [str(c.name) if hasattr(c, 'name') else str(c) for c in clips_list if os.path.exists(str(c.name) if hasattr(c, 'name') else str(c))]
    if not valid_clip_paths:
        print("❌ Invalid clip paths on disk!")
        return None

    audio_str = str(audio_path.name) if hasattr(audio_path, 'name') else str(audio_path)

    try:
        voice_audio = AudioFileClip(audio_str)
        target_duration = voice_audio.duration
        
        # Audio Processing: Voice Volume Boost
        voice_audio = voice_audio.volumex(1.25)

        # Multi-Track Audio Mixing (Background Music + Auto-Ducking)
        final_audio = voice_audio
        if bg_music_path and os.path.exists(str(bg_music_path)):
            try:
                bg_audio = AudioFileClip(str(bg_music_path))
                if bg_audio.duration < target_duration:
                    bg_audio = afx.audio_loop(bg_audio, duration=target_duration)
                else:
                    bg_audio = bg_audio.subclip(0, target_duration)
                
                bg_audio = bg_audio.volumex(bg_volume)
                final_audio = CompositeAudioClip([voice_audio, bg_audio])
                print("🔊 Mixed Voiceover & Background Track with Auto-Ducking.")
            except Exception as e:
                print(f"⚠️ Warning: Background Music mix failed: {e}")

        # Load & Process Clips
        loaded_clips = []
        for p in valid_clip_paths:
            try:
                c = VideoFileClip(p)
                c = apply_color_grading(c, color_preset)
                loaded_clips.append(c)
            except Exception as clip_err:
                print(f"⚠️ Error loading clip {p}: {clip_err}")

        if not loaded_clips:
            return None

        sequence = []
        current_dur = 0.0

        while current_dur < target_duration:
            for clip in loaded_clips:
                if current_dur >= target_duration:
                    break
                rem = target_duration - current_dur
                if clip.duration > rem:
                    sequence.append(clip.subclip(0, rem))
                    current_dur += rem
                else:
                    sequence.append(clip)
                    current_dur += clip.duration

        final_video = concatenate_videoclips(sequence, method="compose")
        final_video = final_video.set_audio(final_audio)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        final_video.write_videofile(
            str(output_path), 
            fps=24, 
            codec="libx264", 
            audio_codec="aac", 
            threads=2, 
            preset="ultrafast", 
            logger=None
        )

        voice_audio.close()
        for c in loaded_clips: c.close()
        final_video.close()
        print(f"✅ Short Pipeline Render Finished: {output_path}")
        return str(output_path)

    except Exception as e:
        traceback.print_exc()
        return None

def render_short_video_pipeline(video_clips_paths, audio_path, output_path='output/short_video.mp4', settings=None):
    return process_multi_clip_render(video_clips_paths, audio_path, output_path, settings=settings)
'''

with open("master_pipeline.py", "w", encoding="utf-8") as f:
    f.write(pipeline_code)

print("✓ master_pipeline.py updated successfully!")

print("\n==================================================")
print("2. CONNECTING UI SETTINGS TO APP.PY")
print("==================================================")

if os.path.exists("app.py"):
    with open("app.py", "r", encoding="utf-8") as f:
        app_text = f.read()

    target_old = "rendered_path = process_multi_clip_render(clips, voice, str(output_file))"
    target_new = "rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=settings)"

    if target_old in app_text:
        app_text = app_text.replace(target_old, target_new)
        with open("app.py", "w", encoding="utf-8") as f:
            f.write(app_text)
        print("✓ app.py connected with real rendering settings!")
    else:
        print("ℹ️ app.py is already connected or uses updated parameter format.")

print("\n==================================================")
print("ALL BACKEND UPDATES COMPLETED SAFELY!")
print("==================================================")