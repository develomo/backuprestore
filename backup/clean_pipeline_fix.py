import os
import shutil

pipeline_file = "master_pipeline.py"

if not os.path.exists(pipeline_file):
    print("❌ Error: master_pipeline.py nahi mili.")
    exit()

# Backup
shutil.copy(pipeline_file, "master_pipeline.py.final_bak")

with open(pipeline_file, "r", encoding="utf-8", errors="ignore") as f:
    code = f.read()

# Clean outdated/duplicate write blocks inside master_pipeline.py
if "def process_multi_clip_render" in code:
    base_part = code.split("def process_multi_clip_render")[0]
else:
    print("❌ Error: process_multi_clip_render start tag missing.")
    exit()

# Reconstruct clean, robust process_multi_clip_render function
clean_function = '''def process_multi_clip_render(clips_list, audio_path, output_path, settings=None):
    import os
    import shutil
    import numpy as np
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

    print("\\n======================================================================")
    print("🎬 MASTER CREATORFLOW SHORT VIDEO ENGINE - CLEAN RENDER")
    print("======================================================================\\n")

    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # 1. Load Audio
    voice_audio = AudioFileClip(audio_path)
    target_duration = voice_audio.duration
    print(f"[STEP 1/5] Voice Audio Loaded (Duration: {target_duration:.2f}s)")

    # 2. Process Video Clips
    loaded_clips = []
    for cp in clips_list:
        if os.path.exists(cp):
            try:
                clip = VideoFileClip(cp)
                loaded_clips.append(clip)
            except Exception as e:
                print(f"[WARN] Could not load clip {cp}: {e}")

    if not loaded_clips:
        raise FileNotFoundError("No valid video clips were loaded.")

    # Concatenate clips to match audio duration
    combined_video = concatenate_videoclips(loaded_clips, method="compose")
    if combined_video.duration < target_duration:
        combined_video = combined_video.loop(duration=target_duration)
    else:
        combined_video = combined_video.subclip(0, target_duration)

    final_video = combined_video.set_audio(voice_audio)

    # 3. Write Base Video to Disk (File Lock Safe)
    temp_export = output_path.replace(".mp4", "_temp_raw.mp4")
    if os.path.exists(temp_export):
        try:
            os.remove(temp_export)
        except Exception:
            pass

    print("\\n[EXPORT] WRITING FINAL MP4 FILE TO DISK...")
    final_video.write_videofile(
        temp_export,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        preset="medium"
    )

    # Close clips to release Windows locks
    try:
        final_video.close()
        voice_audio.close()
        for c in loaded_clips:
            c.close()
    except Exception:
        pass

    # 4. Burn-in Captions / Subtitles if enabled
    captions_applied = False
    if os.path.exists(temp_export):
        try:
            cfg = settings.get('caption_config', {}) if settings else {"enabled": True}
            if cfg.get('enabled', True) and 'process_video_with_captions' in globals():
                print("\\n[STEP 6/6] BURNING DYNAMIC SUBTITLES INTO MP4...")
                process_video_with_captions(temp_export, cfg, output_path)
                captions_applied = True
                print("[CAPTION ENGINE] Subtitles successfully burned into MP4!")
        except Exception as cap_err:
            print(f"[WARN] Caption burn failed: {cap_err}")

    # Move file if captions skipped or failed
    if not captions_applied or not os.path.exists(output_path):
        if os.path.exists(temp_export):
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            shutil.move(temp_export, output_path)

    if os.path.exists(temp_export):
        try:
            os.remove(temp_export)
        except Exception:
            pass

    print("\\n======================================================================")
    print("[SUCCESS] RENDER COMPLETE!")
    print(f"🎯 Output File: {output_path}")
    print("======================================================================\\n")

    return output_path
'''

final_pipeline_code = base_part + "\n\n" + clean_function

import ast
try:
    ast.parse(final_pipeline_code)
    with open(pipeline_file, "w", encoding="utf-8") as f:
        f.write(final_pipeline_code)
    print("🚀 SUCCESS: master_pipeline.py completely rebuilt and verified!")
except SyntaxError as syn_err:
    print(f"❌ Syntax Error: {syn_err}")