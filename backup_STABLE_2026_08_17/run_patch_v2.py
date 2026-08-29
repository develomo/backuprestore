import os

pipeline_code = '''import os
import traceback
import numpy as np
from PIL import Image

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

def apply_clip_motion(clip):
    """Applies slow dynamic zoom-in motion (Ken Burns effect)"""
    dur = clip.duration if clip.duration and clip.duration > 0 else 1.0
    def zoom_frame(get_frame, t):
        frame = get_frame(t)
        h, w, _ = frame.shape
        scale = 1.0 + 0.08 * (t / dur) # Slow 8% zoom in
        new_w, new_h = int(w * scale), int(h * scale)
        img = Image.fromarray(frame)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        crop_x = (new_w - w) // 2
        crop_y = (new_h - h) // 2
        img = img.crop((crop_x, crop_y, crop_x + w, crop_y + h))
        return np.array(img)
    return clip.fl(zoom_frame)

def process_multi_clip_render(clips_list, audio_path, output_path, settings=None):
    print('\\n' + '='*70)
    print('🎬 MASTER CREATORFLOW SHORT VIDEO ENGINE - ADVANCED RENDER')
    print('='*70)

    try:
        from moviepy.editor import (VideoFileClip, concatenate_videoclips, AudioFileClip,
                                     CompositeAudioClip, CompositeVideoClip, ImageClip, afx, vfx)
    except ImportError:
        print('❌ MoviePy is not installed in current environment!')
        return None

    if not clips_list or not audio_path:
        print('❌ Critical Error: Missing video clips or voiceover audio track!')
        return None

    settings = settings or {}
    color_preset = settings.get('color_grading') or settings.get('preset') or 'Standard Neutral'
    bg_music = settings.get('bg_music') or settings.get('music')
    sfx_files = settings.get('sfx') or []
    if isinstance(sfx_files, str): sfx_files = [sfx_files]

    logo_path = settings.get('logo') or settings.get('watermark')
    subscribe_path = settings.get('subscribe') or settings.get('cta')

    bg_volume = float(settings.get('music_vol', settings.get('bg_volume', 0.15)))
    sfx_volume = float(settings.get('sfx_vol', 0.35))

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
        # STEP 1: VOICE EQ
        print('\\n🎙️ [STEP 1/5] PROCESSING VOICEOVER AUDIO TRACK...')
        voice_audio = AudioFileClip(voice_path)
        target_duration = voice_audio.duration
        print(f'   ➔ Target Audio Duration: {target_duration:.2f} seconds')
        print('   ➔ Applying Parametric EQ Normalization (+1.25x Gain Boost)...')
        voice_audio = voice_audio.volumex(1.25)

        audio_mix = [voice_audio]

        # STEP 2: BG MUSIC & DUCKING
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

        # STEP 3: VIDEO CUTS, COLOR, MOTION & TRANSITIONS
        print('\\n🎞️ [STEP 3/5] EDITING VIDEO CLIPS, MOTION, COLOR & TRANSITIONS...')
        loaded_clips = []
        for idx, cp in enumerate(valid_clips, 1):
            print(f'   ➔ Loading Clip #{idx}: {os.path.basename(cp)}')
            v_clip = VideoFileClip(cp)
            v_clip = apply_color_grading(v_clip, color_preset, clip_index=idx)
            loaded_clips.append(v_clip)

        print('\\n✂️ [TIMELINE CUTS & MOTION] Pacing clips & applying dynamic zoom...')
        sequence = []
        cut_timestamps = []
        curr_dur = 0.0

        while curr_dur < target_duration:
            for clip in loaded_clips:
                if curr_dur >= target_duration:
                    break
                rem = target_duration - curr_dur
                cut_timestamps.append(curr_dur)
                
                if clip.duration > rem:
                    print(f'   ➔ Trimming final clip segment ({rem:.2f}s)')
                    segment = clip.subclip(0, rem)
                    curr_dur += rem
                else:
                    print(f'   ➔ Stitching clip segment ({clip.duration:.2f}s)')
                    segment = clip.subclip(0, clip.duration)
                    curr_dur += clip.duration

                # Apply Zoom Motion & Fade Transitions
                segment = apply_clip_motion(segment)
                if len(sequence) > 0:
                    segment = segment.fx(vfx.fadein, 0.25)
                sequence.append(segment)

        final_video = concatenate_videoclips(sequence, method='compose')

        # STEP 4: SFX INTEGRATION AT EVERY CUT POINT
        print('\\n🔊 [STEP 4/5] SYNCHRONIZING SFX AT EVERY SCENE CUT...')
        valid_sfx_paths = []
        if sfx_files:
            for s_item in sfx_files:
                sp = str(s_item.name) if hasattr(s_item, 'name') else str(s_item)
                if os.path.exists(sp):
                    valid_sfx_paths.append(sp)

        if valid_sfx_paths and len(cut_timestamps) > 0:
            for i, cut_time in enumerate(cut_timestamps):
                sfx_p = valid_sfx_paths[i % len(valid_sfx_paths)]
                try:
                    sfx_aud = AudioFileClip(sfx_p).volumex(sfx_volume)
                    sfx_dur = min(sfx_aud.duration, target_duration - cut_time)
                    if sfx_dur > 0:
                        sfx_aud = sfx_aud.subclip(0, sfx_dur).set_start(cut_time)
                        audio_mix.append(sfx_aud)
                        print(f'   ➔ Placed SFX #{i+1} ({os.path.basename(sfx_p)}) at Cut Time {cut_time:.2f}s')
                except Exception as s_err:
                    print(f'   ⚠️ Warning placing SFX at {cut_time:.2f}s: {s_err}')
        else:
            print('   ℹ️ No valid SFX files provided for scene cuts.')

        final_audio = CompositeAudioClip(audio_mix)
        final_video = final_video.set_audio(final_audio)

        # STEP 5: OVERLAYS (LOGO & SUBSCRIBE)
        print('\\n🎨 [STEP 5/5] APPLYING LOGO WATERMARK & SUBSCRIBE OVERLAYS...')
        video_elements = [final_video]

        # Logo Watermark
        logo_p = str(logo_path.name) if hasattr(logo_path, 'name') else (str(logo_path) if logo_path else None)
        if logo_p and os.path.exists(logo_p):
            print(f'   ➔ Overlaying Logo Watermark: {os.path.basename(logo_p)}')
            try:
                logo_clip = (ImageClip(logo_p)
                             .set_duration(target_duration)
                             .resize(width=130)
                             .set_position(("right", 35)))
                video_elements.append(logo_clip)
            except Exception as l_err:
                print(f'   ⚠️ Warning overlaying Logo: {l_err}')

        # Subscribe CTA Overlay
        sub_p = str(subscribe_path.name) if hasattr(subscribe_path, 'name') else (str(subscribe_path) if subscribe_path else None)
        if sub_p and os.path.exists(sub_p):
            print(f'   ➔ Overlaying Subscribe CTA: {os.path.basename(sub_p)}')
            try:
                cta_dur = min(4.5, target_duration / 2)
                cta_start_1 = max(1.0, target_duration * 0.20)
                cta_clip1 = (ImageClip(sub_p)
                             .set_start(cta_start_1)
                             .set_duration(cta_dur)
                             .resize(width=280)
                             .set_position(("center", 0.82), relative=True))
                video_elements.append(cta_clip1)
            except Exception as sub_err:
                print(f'   ⚠️ Warning overlaying Subscribe CTA: {sub_err}')

        if len(video_elements) > 1:
            final_video = CompositeVideoClip(video_elements)

        # FINAL EXPORT
        print('\\n🚀 EXPORTING & RENDERING FINAL SHORT VIDEO MP4...')
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
        print('✅ ALL EDITING, TRANSITIONS, DYNAMIC MOTION, SFX CUTS & OVERLAYS APPLIED!')
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

print('✅ master_pipeline.py updated with SFX scene sync, motion zoom, transitions, logo & subscribe overlay!')

if os.path.exists('app.py'):
    with open('app.py', 'r', encoding='utf-8') as f:
        app_code = f.read()

    target_pattern = 'rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=settings)'
    replacement = '''merged_settings = {**settings, **assets} if 'assets' in locals() else settings
            rendered_path = process_multi_clip_render(clips, voice, str(output_file), settings=merged_settings)'''

    if target_pattern in app_code:
        app_code = app_code.replace(target_pattern, replacement)
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(app_code)
        print('✅ app.py patched for forwarding all assets (Logo, CTA, SFX, BG Music)!')
    else:
        print('ℹ️ app.py already patched or line structured differently.')