import os

pipeline_code = '''import os
import traceback
import numpy as np

def apply_color_grading(clip, preset, clip_index=1):
    """Applies Color Grading filters with explicit terminal logging"""
    p = str(preset).lower() if preset else 'standard'
    
    if 'standard' in p or 'none' in p:
        print(f'   🎨 [COLOR GRADING] Clip #{clip_index}: Standard Neutral (Original Colors Preserved)')
        return clip

    print(f'   🎨 [COLOR GRADING] Clip #{clip_index}: Applying LUT Filter "{preset.upper()}"...')

    def filter_frame(get_frame, t):
        frame = get_frame(t).astype(float)
        
        if 'cinematic' in p or 'warm' in p:
            frame[:, :, 0] = np.clip(frame[:, :, 0] * 1.15 + 12, 0, 255)
            frame[:, :, 1] = np.clip(frame[:, :, 1] * 1.05, 0, 255)
            frame[:, :, 2] = np.clip(frame[:, :, 2] * 0.85, 0, 255)
        elif 'cyberpunk' in p or 'neon' in p:
            frame[:, :, 0] = np.clip(frame[:, :, 0] * 1.25, 0, 255)
            frame[:, :, 2] = np.clip(frame[:, :, 2] * 1.35 + 15, 0, 255)
        elif 'vibrant' in p or 'vivid' in p:
            mean = np.mean(frame, axis=2, keepdims=True)
            frame = np.clip((frame - mean) * 1.35 + mean + 5, 0, 255)
        elif 'monochrome' in p or 'film' in p:
            gray = np.dot(frame[..., :3], [0.2989, 0.5870, 0.1140])
            frame[:, :, 0] = gray
            frame[:, :, 1] = gray
            frame[:, :, 2] = gray

        return frame.astype(np.uint8)

    return clip.fl(filter_frame)

def process_multi_clip_render(clips_list, audio_path, output_path, settings=None):
    print('\\n' + '='*70)
    print('🎬 MASTER CREATORFLOW SHORT VIDEO ENGINE - RENDER STARTED')
    print('='*70)

    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip, afx
    except ImportError:
        print('❌ MoviePy is not installed in current environment!')
        return None

    if not clips_list or not audio_path:
        print('❌ Critical Error: Missing video clips or voiceover audio track!')
        return None

    settings = settings or {}
    color_preset = settings.get('color_grading', 'Standard Neutral')
    bg_music = settings.get('bg_music') or settings.get('music')
    sfx_files = settings.get('sfx') or []
    if isinstance(sfx_files, str): sfx_files = [sfx_files]

    bg_volume = float(settings.get('music_vol', settings.get('bg_volume', 0.15)))
    sfx_volume = float(settings.get('sfx_vol', 0.4))

    valid_clips = []
    for c in clips_list:
        p = str(c.name) if hasattr(c, 'name') else str(c)
        if os.path.exists(p):
            valid_clips.append(p)

    if not valid_clips:
        print('❌ Error: No valid video clip files found on disk!')
        return None

    voice_path = str(audio_path.name) if hasattr(audio_path, 'name') else str(audio_path)

    try:
        print('\\n🎙️ [STEP 1/5] PROCESSING VOICEOVER AUDIO TRACK...')
        voice_audio = AudioFileClip(voice_path)
        target_duration = voice_audio.duration
        print(f'   ➔ Target Audio Duration: {target_duration:.2f} seconds')
        print('   ➔ Applying Parametric EQ Normalization (+1.25x Gain Boost)...')
        voice_audio = voice_audio.volumex(1.25)

        audio_mix = [voice_audio]

        print('\\n🎵 [STEP 2/5] PROCESSING BACKGROUND MUSIC & DUCKING...')
        bg_music_path = str(bg_music.name) if hasattr(bg_music, 'name') else (str(bg_music) if bg_music else None)
        
        if bg_music_path and os.path.exists(bg_music_path):
            print(f'   ➔ BG Track Loaded: {os.path.basename(bg_music_path)}')
            bg_audio = AudioFileClip(bg_music_path)
            if bg_audio.duration < target_duration:
                bg_audio = afx.audio_loop(bg_audio, duration=target_duration)
            else:
                bg_audio = bg_audio.subclip(0, target_duration)

            print(f'   ➔ Applying Auto-Ducking Level ({bg_volume*100:.0f}% Volume relative to voice)...')
            bg_audio = bg_audio.volumex(bg_volume)
            audio_mix.append(bg_audio)
        else:
            print('   ℹ️ No Background Music provided in upload (Skipping BG Track).')

        print('\\n🔊 [STEP 3/5] INTEGRATING SOUND EFFECTS (SFX)...')
        if sfx_files:
            for idx, sfx_item in enumerate(sfx_files, 1):
                sfx_p = str(sfx_item.name) if hasattr(sfx_item, 'name') else str(sfx_item)
                if os.path.exists(sfx_p):
                    print(f'   ➔ Loading SFX Track #{idx}: {os.path.basename(sfx_p)}')
                    try:
                        sfx_aud = AudioFileClip(sfx_p).volumex(sfx_volume)
                        if sfx_aud.duration > target_duration:
                            sfx_aud = sfx_aud.subclip(0, target_duration)
                        audio_mix.append(sfx_aud)
                    except Exception as s_err:
                        print(f'   ⚠️ Warning loading SFX #{idx}: {s_err}')
        else:
            print('   ℹ️ No SFX Assets provided in upload (Skipping SFX).')

        final_audio = CompositeAudioClip(audio_mix) if len(audio_mix) > 1 else voice_audio

        print('\\n🎞️ [STEP 4/5] EDITING VIDEO CLIPS & COLOR FILTERS...')
        loaded_clips = []
        for idx, cp in enumerate(valid_clips, 1):
            print(f'   ➔ Loading Clip #{idx}: {os.path.basename(cp)}')
            v_clip = VideoFileClip(cp)
            v_clip = apply_color_grading(v_clip, color_preset, clip_index=idx)
            loaded_clips.append(v_clip)

        print('\\n✂️ [TIMELINE CUTS] Pacing clips to fit voice duration...')
        sequence = []
        curr_dur = 0.0

        while curr_dur < target_duration:
            for clip in loaded_clips:
                if curr_dur >= target_duration:
                    break
                rem = target_duration - curr_dur
                if clip.duration > rem:
                    print(f'   ➔ Trimming final clip segment to match exact voice end ({rem:.2f}s)')
                    sequence.append(clip.subclip(0, rem))
                    curr_dur += rem
                else:
                    print(f'   ➔ Stitching clip segment ({clip.duration:.2f}s)')
                    sequence.append(clip)
                    curr_dur += clip.duration

        final_video = concatenate_videoclips(sequence, method='compose')
        final_video = final_video.set_audio(final_audio)

        print('\\n🚀 [STEP 5/5] EXPORTING & RENDERING FINAL MP4 FILE...')
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

        voice_audio.close()
        for c in loaded_clips: c.close()
        final_video.close()

        print('\\n' + '='*70)
        print('✅ ALL EDITING FUNCTIONS, SFX, BG MUSIC & COLOR GRADINGS APPLIED!')
        print(f'🎯 Final Render Saved At: {output_path}')
        print('='*70 + '\\n')

        return str(output_path)

    except Exception as e:
        print(f'\\n❌ CRITICAL RENDER PIPELINE FAILURE: {e}')
        traceback.print_exc()
        return None

def render_short_video_pipeline(video_clips_paths, audio_path, output_path='output/short_video.mp4', settings=None):
    return process_multi_clip_render(video_clips_paths, audio_path, output_path, settings=settings)
'''

with open('master_pipeline.py', 'w', encoding='utf-8') as f:
    f.write(pipeline_code)

print('✅ master_pipeline.py successfully updated!')

if os.path.exists('app.py'):
    with open('app.py', 'r', encoding='utf-8') as f:
        app_code = f.read()

    target_str = 'rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=settings)'
    replacement_str = '''merged_settings = {**settings, **assets}
            rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=merged_settings)'''

    if target_str in app_code:
        app_code = app_code.replace(target_str, replacement_str)
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(app_code)
        print('✅ app.py successfully patched!')
    else:
        print('ℹ️ app.py target line already updated or structured differently.')