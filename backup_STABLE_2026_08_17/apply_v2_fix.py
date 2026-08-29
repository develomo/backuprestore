import ast
import os
import shutil

# 1. Backups with V2 tag
for f in ["master_pipeline.py", "app.py"]:
  if os.path.exists(f):
    shutil.copy(f, f"{f}.bak_v2")
    print(f"📦 Created backup: {f}.bak_v2")

# 2. Master Pipeline Updated Code
master_pipeline_code = '''# -*- coding: utf-8 -*-
import os
import sys
import glob
import shutil
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips,
    CompositeAudioClip, ImageClip, afx
)

def hex_to_rgb(hex_str, default=(255, 255, 255)):
    if not hex_str or not isinstance(hex_str, str):
        return default
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        try:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            return default
    return default

def generate_subtitle_segments(audio_path, caption_type="phrase"):
    """Generates precise timestamped subtitle segments from audio using Whisper."""
    segments = []
    try:
        import whisper
        print(f"   ➔ Transcribing voice audio with Whisper (Mode: {caption_type})...")
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, word_timestamps=True)
        
        cap_type = str(caption_type).lower()

        if "word" in cap_type: # Word by Word
            for seg in result.get("segments", []):
                for w in seg.get("words", []):
                    segments.append({
                        "start": float(w["start"]),
                        "end": float(w["end"]),
                        "text": w["word"].strip().upper()
                    })
        elif "line" in cap_type: # Line mode (groups ~5-7 words)
            for seg in result.get("segments", []):
                words = seg.get("words", [])
                if not words:
                    segments.append({
                        "start": float(seg["start"]),
                        "end": float(seg["end"]),
                        "text": seg["text"].strip().upper()
                    })
                    continue
                
                chunk_size = 6
                for i in range(0, len(words), chunk_size):
                    chunk = words[i:i+chunk_size]
                    chunk_text = " ".join([w["word"].strip() for w in chunk]).upper()
                    segments.append({
                        "start": float(chunk[0]["start"]),
                        "end": float(chunk[-1]["end"]),
                        "text": chunk_text
                    })
        else: # Phrase Mode (Default)
            for seg in result.get("segments", []):
                segments.append({
                    "start": float(seg["start"]),
                    "end": float(seg["end"]),
                    "text": seg["text"].strip().upper()
                })
                
        print(f"   [CAPTION ENGINE]: Generated {len(segments)} caption segments for '{caption_type}' mode.")
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

    # Extract UI Styles
    font_size_ratio = float(style_config.get("font_size_ratio", 0.038))
    font_size = max(20, int(height * font_size_ratio))
    text_color = style_config.get("text_color", (255, 255, 0))
    stroke_color = style_config.get("stroke_color", (0, 0, 0))
    bg_color = style_config.get("bg_color", (0, 0, 0, 180))
    use_box = style_config.get("use_box", True)

    # Load System Font
    font = None
    font_paths = [
        "C:\\\\Windows\\\\Fonts\\\\arialbd.ttf",
        "C:\\\\Windows\\\\Fonts\\\\arial.ttf",
        "C:\\\\Windows\\\\Fonts\\\\impact.ttf"
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

    # Wrap Text to avoid going outside boundaries
    max_chars_per_line = max(12, int(width / (font_size * 0.55)))
    wrapped_lines = textwrap.wrap(active_text, width=max_chars_per_line)

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

    start_y = height - total_text_h - int(height * 0.15)

    padding = 12
    if use_box and bg_color:
        rect_x1 = (width - max_line_w) / 2 - padding
        rect_y1 = start_y - padding
        rect_x2 = (width + max_line_w) / 2 + padding
        rect_y2 = start_y + total_text_h + padding
        draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], fill=bg_color)

    current_y = start_y
    for i, line in enumerate(wrapped_lines):
        line_w = line_widths[i]
        line_x = (width - line_w) / 2

        stroke_w = 2
        for ox in range(-stroke_w, stroke_w + 1):
            for oy in range(-stroke_w, stroke_w + 1):
                draw.text((line_x + ox, current_y + oy), line, font=font, fill=stroke_color)

        draw.text((line_x, current_y), line, font=font, fill=text_color)
        current_y += line_h + line_spacing

    return np.array(img)

def apply_green_screen_mask(cta_clip):
    """Safely removes solid green screen background from Subscribe CTA clips."""
    try:
        def make_mask(frame):
            r = frame[:, :, 0].astype(float)
            g = frame[:, :, 1].astype(float)
            b = frame[:, :, 2].astype(float)
            is_green = (g > 80) & (g > r * 1.15) & (g > b * 1.15)
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
    print("MASTER CREATORFLOW BATCH & RENDER PIPELINE - V2 OPTIMIZED")
    print("======================================================================\\n")

    if settings is None:
        settings = {}

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # 1. VOICE AUDIO
    print("[STEP 1/5] VOICE AUDIO PROCESSING...")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Voice audio file missing: {audio_path}")

    voice_audio = AudioFileClip(audio_path)
    target_duration = voice_audio.duration
    print(f"   ➔ Target Audio Duration: {target_duration:.2f}s")

    try:
        boosted_voice = voice_audio.volumex(1.25)
        if target_duration > 0.5:
            boosted_voice = boosted_voice.audio_fadeout(0.4)
    except Exception:
        boosted_voice = voice_audio

    final_audio_tracks = [boosted_voice]

    # 2. BACKGROUND MUSIC
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
            print(f'   [APPLIED]: BG Music Ducked at {int(bg_volume*100)}% Volume')
        except Exception as bg_err:
            print(f"   [WARN] BG Music load failed: {bg_err}")

    # 3. VIDEO CLIPS PACING (FIXED WinError 1455 MEMORY LEAK WITH audio=False)
    print("\\n[STEP 3/5] PACING AND LOADING CLIPS SAFELY...")
    valid_clips = [c for c in clips_list if os.path.exists(c)]
    if not valid_clips:
        raise FileNotFoundError("No valid video clips found on disk.")

    loaded_video_clips = []
    cut_timestamps = [0.0]
    num_clips = len(valid_clips)
    clip_dur = target_duration / num_clips if num_clips > 0 else target_duration

    current_time = 0.0
    for idx, cp in enumerate(valid_clips):
        # audio=False stops FFmpeg from creating extra audio processes per clip!
        vc = VideoFileClip(cp, audio=False)
        if vc.duration < clip_dur:
            vc = vc.loop(duration=clip_dur)
        else:
            vc = vc.subclip(0, clip_dur)

        loaded_video_clips.append(vc)
        current_time += clip_dur
        if idx < num_clips - 1:
            cut_timestamps.append(round(current_time, 2))

    combined_video = concatenate_videoclips(loaded_video_clips, method="compose")
    if combined_video.duration < target_duration:
        combined_video = combined_video.loop(duration=target_duration)
    combined_video = combined_video.subclip(0, target_duration)

    # 4. SFX SYNCHRONIZATION
    sfx_files = settings.get("sfx_files") or settings.get("sfx_list") or []
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
                except Exception:
                    pass

    final_audio = CompositeAudioClip(final_audio_tracks).set_duration(target_duration)
    final_video = combined_video.set_audio(final_audio)

    # 5. OVERLAYS (LOGO & SUBSCRIBE CTA)
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
        except Exception:
            pass

    cta_path = settings.get("cta_path") or settings.get("subscribe_overlay") or settings.get("cta")
    if not cta_path or not os.path.exists(str(cta_path)):
        possible_ctas = glob.glob("*subscribe*.mp4") + glob.glob("*cta*.mp4") + glob.glob("assets/*subscribe*.mp4")
        if possible_ctas:
            cta_path = possible_ctas[0]

    if cta_path and os.path.exists(str(cta_path)):
        try:
            cta_start = target_duration * 0.15
            cta_raw = VideoFileClip(str(cta_path), audio=False).resize(width=380)
            if cta_raw.duration > (target_duration - cta_start):
                cta_raw = cta_raw.subclip(0, target_duration - cta_start)
            cta_clean = apply_green_screen_mask(cta_raw)
            cta_clean = cta_clean.set_start(cta_start).set_position(("center", "bottom")).margin(bottom=50, opacity=0)
            overlay_clips.append(cta_clean)
            print(f"   [APPLIED]: Green Screen Removed Subscribe Overlay ({os.path.basename(str(cta_path))})")
        except Exception as cta_err:
            print(f"   [WARN] Subscribe Overlay Error: {cta_err}")

    master_composition = CompositeVideoClip(overlay_clips, size=final_video.size)

    # 6. CAPTION GENERATION (WITH UI CONNECTIVITY & OPTIONAL CHECKBOX CHECK)
    enable_captions = settings.get("enable_captions", True)
    
    if enable_captions:
        print("\\n[STEP 6/6] CONNECTING UI CAPTION CONFIGURATION & BURNING...")
        ui_cap_cfg = settings.get("caption_config") or settings.get("captions") or {}
        
        caption_type = ui_cap_cfg.get("caption_type") or ui_cap_cfg.get("mode") or "phrase"
        style_id = ui_cap_cfg.get("style_id", "boxed")
        
        # Color mapping from UI
        text_color_hex = ui_cap_cfg.get("text_color") or "#FFE100"
        bg_color_hex = ui_cap_cfg.get("bg_color") or "#000000"
        
        chosen_style = {
            "text_color": hex_to_rgb(text_color_hex, (255, 235, 0)),
            "stroke_color": (0, 0, 0),
            "bg_color": (*hex_to_rgb(bg_color_hex, (0, 0, 0)), 180),
            "use_box": True if "box" in str(style_id).lower() or ui_cap_cfg.get("use_box") else False,
            "font_size_ratio": float(ui_cap_cfg.get("font_size_ratio", 0.038))
        }

        sub_segments = generate_subtitle_segments(audio_path, caption_type=caption_type)
        
        v_w, v_h = master_composition.size
        final_output_video = master_composition.fl(
            lambda gf, t: draw_subtitles_on_frame(gf(t), t, sub_segments, (v_w, v_h), chosen_style)
        )
        print(f"   [SUCCESS]: UI Captions Burned in '{caption_type.upper()}' mode!")
    else:
        print("\\n[STEP 6/6] CAPTIONS DISABLED BY USER CHECKBOX - SKIPPING BURN-IN.")
        final_output_video = master_composition

    # ENCODING FINAL VIDEO
    print("\\n[EXPORT] ENCODING FINAL MP4 VIDEO...")
    final_output_video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        preset="medium"
    )

    try:
        final_output_video.close()
        master_composition.close()
        final_video.close()
        voice_audio.close()
        for c in loaded_video_clips:
            c.close()
    except Exception:
        pass

    print("======================================================================")
    print(f"[SUCCESS] RENDER COMPLETE: {output_path}")
    print("======================================================================\\n")

    return output_path
'''

with open("master_pipeline.py", "w", encoding="utf-8") as f:
  f.write(master_pipeline_code)
print("✅ Updated master_pipeline.py successfully!")