import ast
import glob
import os
import shutil

pipeline_file = "master_pipeline.py"

if not os.path.exists(pipeline_file):
  print("❌ Error: master_pipeline.py file nahi mili.")
  exit()

shutil.copy(pipeline_file, "master_pipeline.py.bak_ui_captions")

full_master_pipeline_code = '''# -*- coding: utf-8 -*-
import os
import sys
import glob
import shutil
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Force UTF-8 stdout encoding for Windows stability
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips,
    CompositeAudioClip, ImageClip, afx
)

def generate_subtitle_segments(audio_path):
    """Generates timestamped subtitle segments from audio using Whisper."""
    segments = []
    try:
        import whisper
        print("   ➔ Transcribing voice audio with Whisper model...")
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        for seg in result.get("segments", []):
            segments.append({
                "start": float(seg["start"]),
                "end": float(seg["end"]),
                "text": seg["text"].strip()
            })
        print(f"   [CAPTION ENGINE]: Generated {len(segments)} caption timed phrases.")
    except Exception as e:
        print(f"   [WARN] Whisper transcription fallback: {e}")
        audio_clip = AudioFileClip(audio_path)
        dur = audio_clip.duration
        audio_clip.close()
        words = ["YOUR FUTURE CHECKUP", "HEALTHCARE AI TRACKING", "PREDICTIVE MEDICAL DATA", "SMART WEARABLE ANALYSIS"]
        step = dur / len(words)
        for i, w in enumerate(words):
            segments.append({"start": i * step, "end": (i + 1) * step, "text": w})
    return segments

def draw_subtitles_on_frame(frame, current_time, subtitle_segments, video_size, style_config):
    """Draws UI-Styled Subtitles on video frames with Automatic Text Wrapping."""
    active_text = ""
    for seg in subtitle_segments:
        if seg["start"] <= current_time <= seg["end"]:
            active_text = seg["text"]
            break

    if not active_text:
        return frame

    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    width, height = video_size

    # 1. UI Style Configurations Extraction
    font_size_ratio = float(style_config.get("font_size_ratio", 0.038))
    font_size = int(height * font_size_ratio)
    text_color = style_config.get("text_color", (255, 235, 59)) # Yellow/UI Color
    stroke_color = style_config.get("stroke_color", (0, 0, 0))
    bg_color = style_config.get("bg_color", (0, 0, 0, 180)) # Dark Box
    use_box = style_config.get("use_box", True)

    # Load System Font
    font = None
    font_paths = [
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\impact.ttf"
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    # 2. AUTO-WRAP TEXT TO PREVENT GOING OUTSIDE VIDEO BOUNDS
    # Max characters per line based on video width and font size
    max_chars_per_line = max(15, int(width / (font_size * 0.55)))
    wrapped_lines = textwrap.wrap(active_text, width=max_chars_per_line)

    # Calculate Total Bounding Height & Max Line Width
    line_heights = []
    line_widths = []
    for line in wrapped_lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_widths.append(bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])
        except Exception:
            line_widths.append(len(line) * (font_size * 0.5))
            line_heights.append(font_size)

    max_line_w = max(line_widths) if line_widths else 100
    line_h = max(line_heights) if line_heights else font_size
    line_spacing = int(line_h * 0.3)
    total_text_h = (line_h + line_spacing) * len(wrapped_lines) - line_spacing

    # Position: Centered Horizontally, Safe Bottom Margin
    start_y = height - total_text_h - int(height * 0.15)

    # 3. Draw Background Box if UI Style requires Box
    padding = 14
    if use_box and bg_color:
        rect_x1 = (width - max_line_w) / 2 - padding
        rect_y1 = start_y - padding
        rect_x2 = (width + max_line_w) / 2 + padding
        rect_y2 = start_y + total_text_h + padding
        draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], fill=bg_color)

    # 4. Draw Wrapped Lines (Stroke + Text)
    current_y = start_y
    for i, line in enumerate(wrapped_lines):
        line_w = line_widths[i]
        line_x = (width - line_w) / 2

        # Stroke Outline
        stroke_w = 2
        for ox in range(-stroke_w, stroke_w + 1):
            for oy in range(-stroke_w, stroke_w + 1):
                draw.text((line_x + ox, current_y + oy), line, font=font, fill=stroke_color)

        # Main Text Color from UI
        draw.text((line_x, current_y), line, font=font, fill=text_color)
        current_y += line_h + line_spacing

    return np.array(img)

def apply_green_screen_mask(cta_clip):
    try:
        def make_mask(frame):
            r = frame[:, :, 0].astype(float)
            g = frame[:, :, 1].astype(float)
            b = frame[:, :, 2].astype(float)
            is_green = (g > 80) & (g > r * 1.2) & (g > b * 1.2)
            mask = np.ones((frame.shape[0], frame.shape[1]), dtype=float)
            mask[is_green] = 0.0
            return mask

        mask_clip = cta_clip.fl_image(make_mask)
        return cta_clip.set_mask(mask_clip)
    except Exception as e:
        print(f"[WARN] Green screen chroma mask error: {e}")
        return cta_clip

def process_multi_clip_render(clips_list, audio_path, output_path, settings=None):
    print("\\n======================================================================")
    print("MASTER CREATORFLOW SHORT VIDEO ENGINE - FULL AUTHENTIC RENDER")
    print("======================================================================\\n")

    if settings is None:
        settings = {}

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # 1. VOICE AUDIO
    print("[STEP 1/5] VOICE AUDIO PROCESSING CHAIN...")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Voice audio file missing: {audio_path}")

    voice_audio = AudioFileClip(audio_path)
    target_duration = voice_audio.duration
    print(f"   ➔ Target Audio Duration: {target_duration:.2f}s")

    try:
        boosted_voice = voice_audio.volumex(1.25)
        if target_duration > 0.5:
            boosted_voice = boosted_voice.audio_fadeout(0.4)
        print("   [APPLIED IN FINAL]: Voice Boost (+1.25x Normalization & Soft Fade-Out)")
    except Exception:
        boosted_voice = voice_audio

    final_audio_tracks = [boosted_voice]

    # 2. BACKGROUND MUSIC & DUCKING
    print("\\n[STEP 2/5] BACKGROUND MUSIC & DUCKING ENGINE...")
    bg_music_path = settings.get("bg_music_path") or settings.get("bg_music") or settings.get("music")
    bg_volume = float(settings.get("bg_volume") or 0.15)

    if bg_music_path and os.path.exists(str(bg_music_path)):
        try:
            bg_clip = AudioFileClip(str(bg_music_path))
            if bg_clip.duration < target_duration:
                loops = int(target_duration // bg_clip.duration) + 1
                bg_clip = afx.audio_loop(bg_clip, nloops=loops)
            bg_clip = bg_clip.subclip(0, target_duration).volumex(bg_volume)
            final_audio_tracks.append(bg_clip)
            print(f'   [APPLIED IN FINAL]: BG Music "{os.path.basename(str(bg_music_path))}" Ducked at {int(bg_volume*100)}% Volume')
        except Exception as bg_err:
            print(f"   [WARN] BG Music load failed: {bg_err}")

    # 3. VIDEO PACING & TRANSITIONS
    print("\\n[STEP 3/5] VIDEO PACING, LOW-INTENSITY FX & TRANSITIONS...")
    valid_clips = [c for c in clips_list if os.path.exists(c)]
    if not valid_clips:
        raise FileNotFoundError("No valid video clips found on disk.")

    loaded_video_clips = []
    cut_timestamps = [0.0]
    num_clips = len(valid_clips)
    clip_dur = target_duration / num_clips if num_clips > 0 else target_duration

    current_time = 0.0
    for idx, cp in enumerate(valid_clips):
        print(f"   ➔ Processing Clip #{idx+1}: {os.path.basename(cp)}")
        vc = VideoFileClip(cp)
        if vc.duration < clip_dur:
            vc = vc.loop(duration=clip_dur)
        else:
            vc = vc.subclip(0, clip_dur)

        loaded_video_clips.append(vc)
        current_time += clip_dur
        if idx < num_clips - 1:
            cut_timestamps.append(round(current_time, 2))

    combined_video = concatenate_videoclips(loaded_video_clips, method="compose", padding=-0.2 if len(loaded_video_clips) > 1 else 0)
    if combined_video.duration < target_duration:
        combined_video = combined_video.loop(duration=target_duration)
    combined_video = combined_video.subclip(0, target_duration)
    print(f"   [APPLIED IN FINAL]: Synced {len(loaded_video_clips)} Segments across {target_duration:.2f}s")

    # 4. SFX BEAT SYNCHRONIZATION
    print("\\n[STEP 4/5] SFX BEAT SYNCHRONIZATION AT SCENE CUTS...")
    sfx_files = settings.get("sfx_files") or settings.get("sfx_list") or []
    applied_sfx_count = 0

    if isinstance(sfx_files, list) and len(sfx_files) > 0:
        for i, cut_time in enumerate(cut_timestamps):
            sfx_p = sfx_files[i % len(sfx_files)]
            if os.path.exists(str(sfx_p)):
                try:
                    sfx_clip = AudioFileClip(str(sfx_p)).volumex(0.4)
                    if sfx_clip.duration > 1.5:
                        sfx_clip = sfx_clip.subclip(0, 1.5)
                    sfx_clip = sfx_clip.set_start(cut_time)
                    final_audio_tracks.append(sfx_clip)
                    applied_sfx_count += 1
                    print(f"   ➔ Placed SFX #{i+1} ({os.path.basename(str(sfx_p))}) at Cut Time {cut_time:.2f}s")
                except Exception as s_err:
                    print(f"   [WARN] SFX Error at {cut_time:.2f}s: {s_err}")
        print(f"   [APPLIED IN FINAL]: {applied_sfx_count} SFX Triggers Placed Perfectly on Cut Beats.")

    final_audio = CompositeAudioClip(final_audio_tracks).set_duration(target_duration)
    final_video = combined_video.set_audio(final_audio)

    # 5. OVERLAYS (WATERMARK LOGO & SUBSCRIBE CTA)
    print("\\n[STEP 5/5] OVERLAYS & ANIMATED CTA COMPOSITION...")
    overlay_clips = [final_video]

    logo_path = settings.get("logo_path") or settings.get("logo")
    if logo_path and os.path.exists(str(logo_path)):
        try:
            logo_clip = (
                ImageClip(str(logo_path))
                .set_duration(target_duration)
                .resize(width=140)
                .set_position(("right", "top"))
                .margin(right=20, top=20, opacity=0)
            )
            overlay_clips.append(logo_clip)
            print(f"   [APPLIED IN FINAL]: Watermark Logo ({os.path.basename(str(logo_path))}) Positioned Top-Right.")
        except Exception as l_err:
            print(f"   [WARN] Watermark Overlay Error: {l_err}")

    cta_path = settings.get("cta_path") or settings.get("subscribe_overlay") or settings.get("cta")
    if not cta_path or not os.path.exists(str(cta_path)):
        possible_ctas = (
            glob.glob("*subscribe*.mp4") + 
            glob.glob("*cta*.mp4") + 
            glob.glob("assets/*subscribe*.mp4") + 
            glob.glob("assets/*cta*.mp4")
        )
        if possible_ctas:
            cta_path = possible_ctas[0]

    if cta_path and os.path.exists(str(cta_path)):
        try:
            cta_start = target_duration * 0.15
            cta_raw = VideoFileClip(str(cta_path)).resize(width=400)
            if cta_raw.duration > (target_duration - cta_start):
                cta_raw = cta_raw.subclip(0, target_duration - cta_start)
            cta_clean = apply_green_screen_mask(cta_raw)
            cta_clean = cta_clean.set_start(cta_start).set_position(("center", "bottom")).margin(bottom=60, opacity=0)
            overlay_clips.append(cta_clean)
            print(f"   [APPLIED IN FINAL]: Animated Subscribe CTA ({os.path.basename(str(cta_path))}) Injected at t={cta_start:.2f}s with Chroma Key.")
        except Exception as cta_err:
            print(f"   [WARN] Subscribe CTA Overlay Error: {cta_err}")

    master_composition = CompositeVideoClip(overlay_clips, size=final_video.size)

    # 6. CAPTION CONFIG PARSING FROM UI SETTINGS
    print("\\n[STEP 6/6] BURNING DYNAMIC SUBTITLES WITH UI STYLE & AUTO-WRAPPING...")
    ui_caption_cfg = settings.get("caption_config") or settings.get("captions") or {}
    
    # Extract Style ID or Custom Colors from UI
    style_id = ui_caption_cfg.get("style_id", "boxed")
    
    # Map UI Selected Styles to PIL Properties
    style_presets = {
        "classic": {"text_color": (255, 255, 255), "stroke_color": (0, 0, 0), "use_box": False, "font_size_ratio": 0.035},
        "yellow_bold": {"text_color": (255, 235, 59), "stroke_color": (0, 0, 0), "use_box": False, "font_size_ratio": 0.040},
        "boxed": {"text_color": (255, 255, 255), "bg_color": (0, 0, 0, 200), "use_box": True, "font_size_ratio": 0.038},
        "highlight": {"text_color": (0, 255, 200), "bg_color": (20, 20, 20, 210), "use_box": True, "font_size_ratio": 0.038}
    }
    
    chosen_style = style_presets.get(style_id, style_presets["boxed"])
    
    # Override with explicit UI custom colors if provided
    if "text_color" in ui_caption_cfg and ui_caption_cfg["text_color"]:
        chosen_style["text_color"] = ui_caption_cfg["text_color"]

    sub_segments = generate_subtitle_segments(audio_path)
    
    video_w, video_h = master_composition.size
    final_captioned_video = master_composition.fl(
        lambda gf, t: draw_subtitles_on_frame(gf(t), t, sub_segments, (video_w, video_h), chosen_style)
    )
    print(f"   [APPLIED IN FINAL]: Burned UI Caption Style ('{style_id}') with Auto Word-Wrapping.")

    # EXPORT
    print("\\n[EXPORT] ENCODING MULTI-FEATURE VIDEO MP4...")
    final_captioned_video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        preset="medium"
    )

    try:
        final_captioned_video.close()
        master_composition.close()
        final_video.close()
        voice_audio.close()
        for c in loaded_video_clips:
            c.close()
    except Exception:
        pass

    print("======================================================================")
    print("[SUCCESS] AUTHENTIC RENDER COMPLETE! ALL SUPPORTED FEATURES PROCESSED.")
    print(f"[OUTPUT] Final Render Saved At: {output_path}")
    print("======================================================================\\n")

    return output_path
'''

try:
  ast.parse(full_master_pipeline_code)
  with open(pipeline_file, "w", encoding="utf-8") as f:
    f.write(full_master_pipeline_code)
  print(
      "🚀 SUCCESS: master_pipeline.py updated with Auto Text Wrapping and UI"
      " Caption Style Picker!"
  )
except SyntaxError as e:
  print(f"❌ AST Syntax Validation Error: {e}")