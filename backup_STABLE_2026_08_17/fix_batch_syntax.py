import os
import ast

print("🚀 Fixing batch_long_renderer.py cleanly without escaping errors...")

target_file = "batch_long_renderer.py"

clean_code = '''import os
import time
import math
import json
import shutil
import subprocess
from pathlib import Path

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

def render_long_batch_memory(voice_path, clips, output_path, music_path=None, sfx_files=None, intro_path=None, outro_path=None, subscribe_overlay=None, quality="480p", fps=24, batch_size=8, final_quality="480p", add_captions=True, words=None, words_path=None, transcript_text=None, caption_mode="phrase", style_id=None, cleanup=True, preset_overrides=None, custom_logo_path=None, wm_opacity=0.6):
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = out_p.parent / f"long_batch_temp_{int(time.time())}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Get Voice Duration via FFprobe
    cmd_dur = [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(voice_path)]
    r = subprocess.run(cmd_dur, capture_output=True, text=True)
    total_voice_dur = float(json.loads(r.stdout)["format"]["duration"])

    segment_dur = 120.0  # 2-minute batches (~2,880 frames)
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

# Verify Python syntax
try:
    ast.parse(clean_code)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(clean_code)
    print("✅ AST PASSED! batch_long_renderer.py successfully patched without errors.")
except SyntaxError as e:
    print(f"❌ Syntax Error: {e}")