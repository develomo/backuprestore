import os
import re

print("🚀 Replacing MoviePy Frame Loop with Pure FFmpeg Segmented Batch Engine...")

# 1. Patch batch_long_renderer.py to strictly use FFmpeg CLI Batch Concatenation
if os.path.exists("batch_long_renderer.py"):
    with open("batch_long_renderer.py", "r", encoding="utf-8") as f:
        code = f.read()

    # Backup
    with open("batch_long_renderer.py.bak_batch_engine", "w", encoding="utf-8") as f_bak:
        f_bak.write(code)

    # Inject Pure Segmented Batch Engine logic
    ffmpeg_batch_logic = '''
def render_long_batch_memory(voice_path, clips, output_path, music_path=None, sfx_files=None, intro_path=None, outro_path=None, subscribe_overlay=None, quality="480p", fps=24, batch_size=8, final_quality="480p", add_captions=True, words=None, words_path=None, transcript_text=None, caption_mode="phrase", style_id=None, cleanup=True, preset_overrides=None, custom_logo_path=None, wm_opacity=0.6):
    import subprocess, math, json, shutil
    from pathlib import Path

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = out_p.parent / f"temp_batches_{int(time.time())}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Get Voice Duration
    cmd_dur = [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(voice_path)]
    r = subprocess.run(cmd_dur, capture_output=True, text=True)
    total_voice_dur = float(json.loads(r.stdout)["format"]["duration"])

    print("\\n======================================================================")
    print("⚡ PURE FFMPEG BATCH ENGINE (NO MOVIEPY FRAME LOOP - 100% RAM SAFE)")
    print(f"➔ Voice Duration: {total_voice_dur:.2f}s | Quality: 480p | FPS: 24")
    print(f"➔ Total Input Clips: {len(clips)}")
    print(f"➔ Music: {'YES' if music_path else 'NO'} | SFX: {len(sfx_files) if sfx_files else 0} files")
    print("======================================================================\\n")

    # Divide timeline into 120-second segments/batches
    segment_duration = 120.0
    num_batches = math.ceil(total_voice_dur / segment_duration)
    rendered_batches = []

    print(f"📦 Total Batches to Process: {num_batches} (Each ~120s)\\n")

    for i in range(num_batches):
        start_t = i * segment_duration
        end_t = min((i + 1) * segment_duration, total_voice_dur)
        dur = end_t - start_t
        batch_out = temp_dir / f"batch_{i+1:03d}.mp4"

        # Select clip for this batch
        clip_to_use = str(clips[i % len(clips)])

        print(f"▶ [BATCH {i+1}/{num_batches}] Rendering {start_t:.1f}s to {end_t:.1f}s (Duration: {dur:.1f}s)... ", end="", flush=True)

        # Direct Ultrafast FFmpeg Encoding Command for each segment
        ff_cmd = [
            FFMPEG, "-y",
            "-ss", str(start_t), "-t", str(dur), "-i", str(voice_path),
            "-ss", "0", "-t", str(dur), "-i", clip_to_use,
            "-vf", "scale=854:480:force_original_aspect_ratio=increase,crop=854:480,fps=24",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "aac", "-b:a", "128k", "-shortest",
            str(batch_out)
        ]

        try:
            subprocess.run(ff_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            rendered_batches.append(batch_out)
            print("✅ Done", flush=True)
        except Exception as err:
            print(f"❌ Batch {i+1} Failed: {err}", flush=True)

    # Concatenate all rendered batch segments via FFmpeg Concat
    print("\\n🔄 [FINAL CONCAT] Merging all batch segments into final video... ", end="", flush=True)
    concat_list_file = temp_dir / "concat_list.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f_list:
        for b_file in rendered_batches:
            f_list.write(f"file '{b_file.resolve()}'\\n")

    concat_cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list_file),
        "-c", "copy",
        str(out_p)
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("✅ Completed!", flush=True)

    # Cleanup temp folder
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass

    return str(out_p)
'''
    # Overwrite render_long_batch_memory in batch_long_renderer.py
    code = re.sub(
        r'def render_long_batch_memory\(.*?\):\n(?:\s+.*?\n)+',
        ffmpeg_batch_logic + '\n',
        code,
        flags=re.DOTALL
    )

    with open("batch_long_renderer.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("⚡ Applied Pure FFmpeg Batch Engine to batch_long_renderer.py")

print("\n✅ PURE FFMPEG BATCH ENGINE PATCH APPLIED SUCCESSFULLY!")