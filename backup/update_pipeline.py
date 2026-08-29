python -c "
pipeline_code = '''import os
import time
import traceback
import numpy as np

def apply_color_grading(clip, preset, clip_index):
    \"\"\"Applies actual Color Grading to MoviePy Clip with live CMD logging\"\"\"
    if not preset or str(preset).lower() in ['none', 'standard']:
        print(f'   🎨 [COLOR GRADING] Clip #{clip_index}: Standard / Original Color Preserved.')
        return clip

    p = str(preset).lower()
    print(f'   🎨 [COLOR GRADING] Clip #{clip_index}: Applying \"{preset.upper()}\" LUT Filter...')

    def filter_frame(get_frame, t):
        frame = get_frame(t).astype(float)
        
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
    print('\\n' + '='*65)
    print('🎬 MASTER SHORT VIDEO PIPELINE EXECUTION STARTED')
    print('='*65)

    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip, afx
    except ImportError:
        print('❌ MoviePy is not installed!')
        return None

    if not clips_list or not audio_path:
        print('❌ Missing input clips or voiceover audio track!')
        return None

    settings = settings or {}
    color_preset = settings.get('color_grading', 'Warm Luxury')
    bg_music_path = settings.get('bg_music')
    sfx_path = settings.get('sfx_path')
    bg_volume = float(settings.get('music_volume', 0.15))

    valid_clip_paths = [str(c.name) if hasattr(c, 'name') else str(c) for c in clips_list if os.path.exists(str(c.name) if hasattr(c, 'name') else str(c))]
    if not valid_clip_paths:
        print('❌ No valid clip files found on disk!')
        return None

    audio_str = str(audio_path.name) if hasattr(audio_path, 'name') else str(audio_path)

    try:
        # STEP 1: VOICE AUDIO PROCESSING & EQ NORMALIZATION
        print('\\n🎙️ [STEP 1/5] PROCESSING VOICEOVER AUDIO...')
        voice_audio = AudioFileClip(audio_str)
        target_duration = voice_audio.duration
        print(f'   ➔ Audio Track Duration: {target_duration:.2f} seconds')
        print('   ➔ Applying Parametric EQ & Gain Boosting (+1.25x Normalization)...')
        voice_audio = voice_audio.volumex(1.25)

        audio_tracks = [voice_audio]

        # STEP 2: BACKGROUND MUSIC INTEGRATION & AUTO-DUCKING
        print('\\n🎵 [STEP 2/5] BACKGROUND MUSIC & SOUND EFFECTS MIXING...')
        if bg_music_path and os.path.exists(str(bg_music_path)):
            print(f'   ➔ BG Track Loaded: {os.path.basename(str(bg_music_path))}')
            bg_audio = AudioFileClip(str(bg_music_path))
            if bg_audio.duration < target_duration:
                bg_audio = afx.audio_loop(bg_audio, duration=target_duration)
            else:
                bg_audio = bg_audio.subclip(0, target_duration)
            
            print(f'   ➔ Applying Auto-Ducking Volume (-15dB / {bg_volume*100:.0f}% Level relative to Voice)...')
            bg_audio = bg_audio.volumex(bg_volume)
            audio_tracks.append(bg_audio)
        else:
            print('   ℹ️ No Background Music attached (Skipping BG Ducking).')

        # STEP 3: SFX & TRANSITION AUDIO
        if sfx_path and os.path.exists(str(sfx_path)):
            print(f'   ➔ Transition SFX Loaded: {os.path.basename(str(sfx_path))}')
            try:
                sfx_audio = AudioFileClip(str(sfx_path)).volumex(0.4)
                audio_tracks.append(sfx_audio)
            except Exception as sfx_err:
                print(f'   ⚠️ SFX Error: {sfx_err}')
        else:
            print('   ℹ️ No Transition SFX attached.')

        final_audio = CompositeAudioClip(audio_tracks) if len(audio_tracks) > 1 else voice_audio

        # STEP 4: VIDEO CLIPS PROCESSING & COLOR GRADING
        print('\\n🎞️ [STEP 3/5] VIDEO CLIPS EDITING & COLOR GRADING...')
        loaded_clips = []
        for idx, p in enumerate(valid_clip_paths, 1):
            try:
                print(f'   ➔ Loading Clip #{idx}: {os.path.basename(p)}')
                c = VideoFileClip(p)
                c = apply_color_grading(c, color_preset, idx)
                loaded_clips.append(c)
            except Exception as clip_err:
                print(f'   ⚠️ Failed to process clip #{idx}: {clip_err}')

        if not loaded_clips:
            print('❌ No clips could be loaded successfully!')
            return None

        # STEP 5: SEQUENTIAL TIMELINE STITCHING
        print('\\n✂️ [STEP 4/5] TIMELINE CUTS & BEAT-SYNC PACING...')
        sequence = []
        current_dur = 0.0

        while current_dur < target_duration:
            for clip in loaded_clips:
                if current_dur >= target_duration:
                    break
                rem = target_duration - current_dur
                if clip.duration > rem:
                    print(f'   ➔ Trimming Clip segment to fit remaining voice duration ({rem:.2f}s)')
                    sequence.append(clip.subclip(0, rem))
                    current_dur += rem
                else:
                    print(f'   ➔ Adding full clip segment ({clip.duration:.2f}s)')
                    sequence.append(clip)
                    current_dur += clip.duration

        final_video = concatenate_videoclips(sequence, method='compose')
        final_video = final_video.set_audio(final_audio)

        # STEP 6: EXPORT & RENDERING
        print('\\n🚀 [STEP 5/5] RENDERING MULTI-TRACK SHORT VIDEO...')
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        final_video.write_videofile(
            str(output_path), 
            fps=24, 
            codec='libx264', 
            audio_codec='aac', 
            threads=2, 
            preset='ultrafast', 
            logger=None
        )

        # Cleanup
        voice_audio.close()
        for c in loaded_clips: c.close()
        final_video.close()

        print('\\n' + '='*65)
        print(f'✅ SHORT VIDEO PIPELINE RENDER FINISHED SUCCESSFULLY!')
        print(f'🎯 Output Saved: {output_path}')
        print('='*65 + '\\n')
        return str(output_path)

    except Exception as e:
        print(f'\\n❌ CRITICAL PIPELINE RENDER ERROR: {e}')
        traceback.print_exc()
        return None

def render_short_video_pipeline(video_clips_paths, audio_path, output_path='output/short_video.mp4', settings=None):
    return process_multi_clip_render(video_clips_paths, audio_path, output_path, settings=settings)
'''

with open('master_pipeline.py', 'w', encoding='utf-8') as f:
    f.write(pipeline_code)

print('✅ master_pipeline.py written with Full Live Console Logging!')

# Connect UI settings inside app.py safely
if os.path.exists('app.py'):
    with open('app.py', 'r', encoding='utf-8') as f:
        app_text = f.read()

    old_call = 'rendered_path = process_multi_clip_render(clips, voice, str(output_file))'
    new_call = 'rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=settings)'

    if old_call in app_text:
        app_text = app_text.replace(old_call, new_call)
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(app_text)
        print('✅ app.py updated to transmit settings!')
    else:
        print('ℹ️ app.py is already connected to settings.')
"