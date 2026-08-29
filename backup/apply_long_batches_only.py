import os
import re
import ast

print("🚀 Restoring master_pipeline.py and applying Batch Engine strictly to Long Video Pipeline...")

# 1. RESTORE master_pipeline.py to original state (for Short Videos)
if os.path.exists("master_pipeline.py.bak_chunks"):
    with open("master_pipeline.py.bak_chunks", "r", encoding="utf-8") as src, open("master_pipeline.py", "w", encoding="utf-8") as dst:
        dst.write(src.read())
    print("✅ Restored master_pipeline.py back to original (Short video untouched).")

# 2. PATCH app.py -> Ensure Long Video routes ONLY to safe_long_video_polished
if os.path.exists("app.py"):
    with open("app.py", "r", encoding="utf-8") as f:
        app_code = f.read()

    # Route fix interceptor
    long_routing_block = '''
        # LONG VIDEO ROUTER (FFmpeg Batch Engine)
        if ("16:9" in str(selected_format)) or ("Long" in str(selected_format)) or is_long_format:
            import safe_long_video_polished
            return safe_long_video_polished.run_integrated_long_pipeline(
                voice_path=_save_streamlit_upload_to_temp(voice_file) if 'voice_file' in locals() else None,
                clips=[_save_streamlit_upload_to_temp(c) for c in clip_files] if 'clip_files' in locals() and clip_files else [],
                music_path=_save_streamlit_upload_to_temp(music_file) if 'music_file' in locals() else None,
                sfx_files=[_save_streamlit_upload_to_temp(s) for s in sfx_files] if 'sfx_files' in locals() and sfx_files else [],
                intro_path=_save_streamlit_upload_to_temp(intro_file) if 'intro_file' in locals() else None,
                outro_path=_save_streamlit_upload_to_temp(outro_file) if 'outro_file' in locals() else None,
                subscribe_overlay=_save_streamlit_upload_to_temp(long_subscribe_file) if 'long_subscribe_file' in locals() else None,
                custom_logo_path=_save_streamlit_upload_to_temp(logo_file) if 'logo_file' in locals() else None,
                add_captions=add_captions_toggle if 'add_captions_toggle' in locals() else True,
                output_path=str(output_file),
                fps=24,
                quality="480p"
            )
'''
    if "safe_long_video_polished.run_integrated_long_pipeline" not in app_code:
        app_code = app_code.replace(
            "rendered_path = process_multi_clip_render(",
            long_routing_block + "\n        rendered_path = process_multi_clip_render("
        )
        with open("app.py", "w", encoding="utf-8") as f:
            f.write(app_code)
        print("✅ Corrected Long Video routing in app.py.")

# 3. IMPLEMENT BATCH CHUNK ENGINE DIRECTLY IN batch_long_renderer.py
if os.path.exists("batch_long_renderer.py"):
    with open("batch_long_renderer.py", "r", encoding="utf-8") as f:
        batch_code = f.read()

    batch_engine_impl = '''
def render_long_batch_memory(voice_path, clips, output_path, music_path=None, sfx_files=None, intro_path=None, outro_path=None, subscribe_overlay=None, quality="480p", fps=24, batch_size=8, final_quality="480p", add_captions=True, words=None, words_path=None, transcript_text=None, caption_mode="phrase", style_id=None, cleanup=True, preset_overrides=None, custom_logo_path=None, wm_opacity=0.6):
    import subprocess, math, json, shutil, time
    from pathlib import Path

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = out_p.parent / f"long_batch_temp_{int(time.time())}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    FFMPEG = "ffmpeg"
    FFPROBE = "ffprobe"

    # Get Voice Duration
    cmd_dur = [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(voice_path)]
    r = subprocess.run(cmd_dur, capture_output=True, text=True)
    total_voice_dur = float(json.loads(r.stdout)["format"]["duration"])

    segment_dur = 120.0  # 2-minute batches (~2880 frames)
    num_batches = math.ceil(total_voice_dur / segment_dur)

    print("\\n======================================================================")
    print("⚡ LONG VIDEO BATCH ENGINE ACTIVE (NO MOVIEPY FRAME LOOP)")
    print(f"➔ Total Duration: {total_voice_dur:.2f}s (~{total_voice_dur/60:.1f} Mins)")
    print(f"➔ Total Batches: {num_batches} (Each batch ~120s / 2,880 frames)")
    print(f"➔ Input Clips: {len(clips)} | SFX: {len(sfx_files) if sfx_files else 0}")
    print("======================================================================\\n")

    rendered_batches = []

    for i in range(num_batches):
        start_t = i * segment_dur
        end_t = min((i + 1) * segment_dur, total_voice_dur)
        dur = end_t - start_t
        batch_out = temp_dir / f"batch_{i+1:03d}.mp4"

        clip_to_use = str(clips[i % len(clips)])

        print(f"▶ [LONG BATCH {i+1}/{num_batches}] Rendering {start_t:.1f}s to {end_t:.1f}s (~{int(dur*24)} frames)... ", end="", flush=True)

        ff_cmd = [
            FFMPEG, "-y",
            "-ss", str(start_t), "-t", str(dur), "-i", str(voice_path),
            "-ss", "0", "-t", str(dur), "-i", clip_to_use,
            "-vf", "scale=854:480:force_original_aspect_ratio=increase,crop=854:480,fps=24",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "aac", "-b:a", "128k", "-shortest",
            str(batch_out)
        ]

        subprocess.run(ff_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        rendered_batches.append(batch_out)
        print("✅ Done", flush=True)

    print("\\n🔄 [FINAL MERGE] Concatenating long video batch files... ", end="", flush=True)
    concat_list = temp_dir / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f_list:
        for b_file in rendered_batches:
            f_list.write(f"file '{b_file.resolve()}'\\n")

    concat_cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c", "copy",
        str(out_p)
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("✅ Completed!", flush=True)

    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass

    return str(out_p)
'''
    # Replace existing render_long_batch_memory function
    batch_code = re.sub(
        r'def render_long_batch_memory\(.*?\):\n(?:\s+.*?\n)+',
        batch_engine_impl + '\n',
        batch_code,
        flags=re.DOTALL
    )

    # Validate AST
    try:
        ast.parse(batch_code)
        with open("batch_long_renderer.py", "w", encoding="utf-8") as f:
            f.write(batch_code)
        print("✅ Successfully patched batch_long_renderer.py with Batch Chunking Engine.")
    except SyntaxError as e:
        print(f"❌ Syntax Error in batch_long_renderer.py: {e}")

print("\n🎉 LONG VIDEO BATCH PATCH COMPLETED!")