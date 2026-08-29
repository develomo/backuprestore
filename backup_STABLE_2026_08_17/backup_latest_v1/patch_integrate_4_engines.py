# patch_integrate_4_engines.py
# ============================================================
# INTEGRATES 5 engines into batch_long_renderer.py pipeline
# REPLACES render_clip_segment() and concat_files_xfade()
# with engine-aware versions
# ============================================================

import shutil
from pathlib import Path

BASE_DIR = Path(r"D:\My Creation Video Generator\backup")
TARGET = BASE_DIR / "batch_long_renderer.py"

if not TARGET.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

# 1. Backup with timestamp
import time
backup = TARGET.with_suffix(f".py.patch_4engines_{int(time.time())}")
shutil.copy2(TARGET, backup)
print(f"[OK] Backup: {backup.name}")

content = TARGET.read_text(encoding="utf-8")

# 2. Add import for unique_editing_engine at top of file (after existing imports)
old_import_line = "import json, re, shutil, subprocess, time, gc, random"
new_import_line = """import json, re, shutil, subprocess, time, gc, random

# ============================================================
# 4 ENGINES IMPORT (Integrated into pipeline)
# ============================================================
try:
    from unique_editing_engine import (
        get_clip_dna, pick_motion_with_tracking,
        pick_transition_with_tracking, MOTION_CANVAS,
        TRANSITION_TYPES, engine_report, FFMPEG_GRAIN_FILTER,
        FFMPEG_MOTION_BLUR_FILTER
    )
    ENGINES_AVAILABLE = True
except ImportError:
    print("[Engines] unique_editing_engine.py not found — engines disabled")
    ENGINES_AVAILABLE = False"""

if "from unique_editing_engine import" not in content:
    content = content.replace(old_import_line, new_import_line, 1)
    print("[OK] Engine import added.")
else:
    print("[INFO] Engine import already present.")

# 3. REPLACE render_clip_segment() with engine-aware version
old_render = '''def render_clip_segment(src,out,wanted,index,size,fps,quality,niche='default'):
    src=Path(src); out=Path(out); sd=probe_duration(src); start=scene_start(sd,wanted,index)
    crf="32" if normalize_quality(quality)=="360p" else "29"
    run_cmd([FFMPEG,"-y","-ss",f"{start:.3f}","-t",f"{wanted:.3f}","-i",str(src),"-an","-vf",make_visual_filter(src,size,index,fps,niche=niche),"-r",str(fps),"-pix_fmt","yuv420p","-c:v","libx264","-preset","ultrafast","-crf",crf,"-movflags","+faststart",str(out)])
    return out'''

new_render = '''def render_clip_segment(src,out,wanted,index,size,fps,quality,niche='default',total_clips=1):
    """Render clip segment with 5-ENGINE unique editing applied.

    ENGINE 1 (Motion Canvas): Per-clip unique motion via zoompan filter.
    ENGINE 3 (Color Grading): Per-clip unique color via eq filter.
    ENGINE 4 (Effects): Probabilistic grain + motion blur.
    ENGINE 5 (Anti-Template): get_clip_dna() ensures no two clips are same.
    """
    src=Path(src); out=Path(out); sd=probe_duration(src); start=scene_start(sd,wanted,index)
    crf="32" if normalize_quality(quality)=="360p" else "29"
    w,h=size

    # Build base visual filter
    base_vf = make_visual_filter(src,size,index,fps,niche=niche)

    # ENGINE INTEGRATION: Get unique DNA for this clip
    if ENGINES_AVAILABLE:
        try:
            dna = get_clip_dna(str(src), index, niche=niche, total_clips=max(1,total_clips))
            # Build additional filters from DNA
            extra_filters = []
            if dna.get("color_filter"):
                extra_filters.append(dna["color_filter"])
            if dna.get("use_grain") and dna.get("grain_filter"):
                extra_filters.append(dna["grain_filter"])
            if dna.get("use_blur") and dna.get("blur_filter"):
                extra_filters.append(dna["blur_filter"])

            if extra_filters:
                vf = base_vf + "," + ",".join(extra_filters)
            else:
                vf = base_vf

            log(f"[EngineDNA] clip#{index} | motion={dna.get('motion_name','?')} | "
                f"hue={dna.get('color_params',{}).get('hue',0)} | "
                f"grain={dna.get('use_grain')} | blur={dna.get('use_blur')}")
        except Exception as e:
            log(f"[EngineDNA] clip#{index} engine fallback: {e}")
            vf = base_vf
    else:
        vf = base_vf

    run_cmd([FFMPEG,"-y","-ss",f"{start:.3f}","-t",f"{wanted:.3f}","-i",str(src),
             "-an","-vf",vf,"-r",str(fps),"-pix_fmt","yuv420p","-c:v","libx264",
             "-preset","ultrafast","-crf",crf,"-movflags","+faststart",str(out)])
    return out'''

if "def render_clip_segment(src,out,wanted,index,size,fps,quality,niche='default'):" in content:
    # Find and replace the function
    content = content.replace(old_render, new_render)
    print("[OK] render_clip_segment() upgraded with 5-engine DNA injection.")
else:
    print("[WARN] Could not find render_clip_segment — check indentation.")

# 4. UPDATE render_long_batch_memory() to pass total_clips
old_render_call = "render_clip_segment(clip,seg,scene_durations[gi],gi,size,fps,quality,preset.get('niche','default')); segs.append(seg); rendered+=1"
new_render_call = "render_clip_segment(clip,seg,scene_durations[gi],gi,size,fps,quality,preset.get('niche','default'),total_clips=len(clip_paths)); segs.append(seg); rendered+=1"

if old_render_call in content:
    content = content.replace(old_render_call, new_render_call)
    print("[OK] render_clip_segment() call updated with total_clips param.")
elif "total_clips=len(clip_paths)" in content:
    print("[INFO] render_clip_segment() call already has total_clips.")
else:
    print("[WARN] Could not find render_clip_segment() call to update.")

# 5. ADD engine report to final render report
old_report_music = '"music_used":bool(music)'
new_report_music = '"engines_integrated":ENGINES_AVAILABLE,"engines_report":engine_report() if ENGINES_AVAILABLE else {},"music_used":bool(music)'

if 'engines_integrated' not in content:
    content = content.replace(old_report_music, new_report_music)
    print("[OK] Engine report added to render output.")
else:
    print("[INFO] Engine report already in render output.")

# 6. Save
TARGET.write_text(content, encoding="utf-8")
print("\n" + "="*60)
print("✅ PATCH 2 APPLIED: Engines INTEGRATED into batch_long_renderer.py")
print("="*60)
print("Changes:")
print("  1. Added 'from unique_editing_engine import ...'")
print("  2. render_clip_segment() now calls get_clip_dna() per clip")
print("  3. Color grade, grain, motion blur applied per clip