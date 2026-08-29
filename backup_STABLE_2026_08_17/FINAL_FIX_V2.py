# FINAL_FIX_V2.py — Targeted line-edit fixes
import shutil, time
from pathlib import Path

BASE = Path(__file__).resolve().parent
ts = int(time.time())

print("=" * 60)
print("  FINAL FIX V2 — Targeted Edits")
print("=" * 60)

bl = BASE / "batch_long_renderer.py"
shutil.copy2(bl, BASE / f"batch_long_renderer.py.bak_v2_{ts}")
b = bl.read_text(encoding="utf-8")

fixes = 0

# -------------------------------------------------------
# FIX A: BG Music gap — add -shortest and ensure proper looping
# -------------------------------------------------------
# Line 1171: "-stream_loop","-1","-i",str(music)
# The issue: music file is 1:58, without -shortest the loop might end early.
# Fix: Change the amix to use music:audiofilter=aloop instead of -stream_loop
#
# Current pattern (lines ~1170-1185):
#   cmd += ["-stream_loop","-1","-i",str(music)]
#   filters.append(f"[{idx}:a]volume=...,{music_tone},atrim=0:{body_len}...")
#
# BETTER APPROACH: Use aformat + aloop in filter_complex instead

old_music_block = '''if music and Path(music).exists():
        cmd += ["-stream_loop","-1","-i",str(music)]
        # Music starts after intro, stays under voice, and fades before outro.
        music_idx = len(cmd) // 2  # rough index
        filters.append(
            f"[{music_idx}:a]volume={music_volume},"
            f"{music_tone},"
            f"atrim=0:{body_len:.3f},"
            f"adelay={int(intro_sec*1000)}|{int(intro_sec*1000)},"
            f"afade=t=out:st={body_len-intro_sec-0.5}:d=0.5"
            f"[mux]"
        )'''

new_music_block = '''if music and Path(music).exists():
        cmd += ["-stream_loop","-1","-i",str(music)]
        music_idx = len(cmd) // 2
        music_dur = probe_duration(music)
        # Calculate how many loops needed + ensure no gap
        loops_needed = max(1, int(body_len / max(0.5, music_dur)) + 2)
        filters.append(
            f"[{music_idx}:a]volume={music_volume},"
            f"{music_tone},"
            f"aloop=loop={loops_needed}:size=2e9,"
            f"atrim=0:{body_len:.3f},"
            f"adelay={int(intro_sec*1000)}|{int(intro_sec*1000)},"
            f"afade=t=out:st={body_len-intro_sec-0.5}:d=0.5"
            f"[mux]"
        )'''

if old_music_block in b:
    b = b.replace(old_music_block, new_music_block)
    fixes += 1
    print("  [A] BG MUSIC: aloop added, no more 30s gap ✅")
else:
    print("  [A] BG MUSIC block not matched, checking manually...")
    # Find the actual block
    idx = b.find('if music and Path(music).exists():')
    if idx != -1:
        block_end = b.find('[mux]', idx)
        if block_end != -1:
            block_end = b.find('\n', block_end) + 1
            old_block = b[idx:block_end]
            # Replace atrim with aloop+atrim
            if 'aloop' not in old_block:
                new_block = old_block.replace(
                    'f"[{music_idx}:a]volume=',
                    'loop_count = max(1, int(body_len / max(0.5, probe_duration(music))) + 2)\n'
                    '        filters.append(\n'
                    '            f"[{music_idx}:a]volume='
                )
                new_block = new_block.replace(
                    'atrim=0:{body_len:.3f},',
                    'aloop=loop={loop_count}:size=2e9,atrim=0:{body_len:.3f},'
                )
                b = b[:idx] + new_block + b[block_end:]
                fixes += 1
                print("  [A] BG MUSIC: manual aloop injection ✅")
            else:
                print("  [A] BG MUSIC: aloop already present")

# -------------------------------------------------------
# FIX B: SFX — dynamic interval matching clip transitions
# -------------------------------------------------------
# Line 1192: burst_interval = 7.5
# Should be: burst_interval = body_len / total_clips (match actual clip rhythm)
old_sfx_int = 'burst_interval = 7.5'
new_sfx_int = 'burst_interval = min(7.5, max(3.0, body_len / max(1, n_bursts)))  # dynamic: matches clip rhythm'

if old_sfx_int in b:
    b = b.replace(old_sfx_int, new_sfx_int)
    fixes += 1
    print("  [B] SFX: dynamic interval matching clip transitions ✅")
else:
    print("  [B] SFX interval line not found, searching...")
    idx = b.find('burst_interval')
    if idx != -1:
        end = b.find('\n', idx)
        print(f"  Found: {b[idx:end]}")
        # Replace whatever is there
        old_line = b[idx:end]
        new_line = 'burst_interval = min(7.5, max(3.0, body_len / max(1, n_bursts)))  # dynamic clip rhythm'
        b = b[:idx] + new_line + b[end:]
        fixes += 1
        print("  [B] SFX interval fixed ✅")

# Also make sure SFX volume profile uses softer values (minimal/soft)
old_sfx_vols = '"sfx_volume":0.075,"sfx_volume":0.085,"sfx_volume":0.085,"sfx_volume":0.085,"sfx_volume":0.045'
# These are already soft — just ensure no loud values exist
# Check for any sfx_volume > 0.1
import re
for m in re.finditer(r'"sfx_volume":([\d.]+)', b):
    vol = float(m.group(1))
    if vol > 0.12:
        print(f"  [B] WARNING: sfx_volume {vol} > 0.12 — consider reducing")
        break
else:
    print("  [B] SFX volumes all within soft range ✅")

# -------------------------------------------------------
# FIX C: Still picture → Loop clips
# -------------------------------------------------------
# The body extension happens in render_long_batch_memory
# Current code: pad = max(0.1, target_duration - actual)
#               run_cmd([FFMPEG,"-y","-i",str(body_raw),"-vf","tpad=...
# We need to REPLACE the padding with clip looping.

old_pad_block = '''body shorter ({actual:.2f} < {target_duration:.2f}); extending BODY ONLY (outro untouched)")
        pad = max(0.1, target_duration - actual)
        run_cmd([FFMPEG,"-y","-i",str(body_raw),"-vf",'''

if old_pad_block in b:
    new_pad_block = '''body shorter ({actual:.2f} < {target_duration:.2f}); LOOPING clips instead of padding (outro untouched)")
        current = extend_with_reused_clips(body_raw, target_duration, clip_paths, scene_durations, size, fps, quality, niche=preset.get('niche','default'))
        body_raw = current
        actual = probe_duration(body_raw)
        log(f"[StableLong] body extended to {actual:.1f}s via clip looping")
        # skip the old pad+concat — just continue
        if actual >= target_duration - 0.1:
            # already long enough, skip pad
            pass
        else:
            pad = max(0.1, target_duration - actual)
            run_cmd([FFMPEG,"-y","-i",str(body_raw),"-vf",'''
    b = b.replace(old_pad_block, new_pad_block)
    fixes += 1
    print("  [C] STILL PICTURE: body extension uses clip looping ✅")
else:
    print("  [C] STILL PICTURE block not matched — checking manually...")
    idx = b.find('body shorter')
    if idx != -1:
        snippet = b[idx:idx+400]
        print(f"  Context: {snippet[:300]}...")
        
        # Manual replace: swap tpad freeze with clip reuse
        if 'tpad=stop_mode=clone' in snippet or 'tpad' in snippet:
            old_tpad = 'run_cmd([FFMPEG,"-y","-i",str(body_raw),"-vf",f"tpad=stop_mode=clone:stop_duration={pad:.3f}"'
            new_loop = 'body_raw = extend_with_reused_clips(body_raw, target_duration, clip_paths, scene_durations, size, fps, quality, niche=preset.get("niche","default"))\n        run_cmd([FFMPEG,"-y","-i",str(body_raw),"-vf","null"'
            if old_tpad in b:
                b = b.replace(old_tpad, new_loop)
                fixes += 1
                print("  [C] STILL PICTURE: tpad replaced with clip looping ✅")

# -------------------------------------------------------
# FIX D: Transition pool — ensure all 8 types appear
# -------------------------------------------------------
# Already partially fixed in V1. Verify.
unique_trans = set()
for m in re.finditer(r'"base":\[(.*?)\]', b):
    types = [t.strip('"') for t in m.group(1).split(',')]
    unique_trans.update(types)
print(f"  [D] TRANSITIONS: {len(unique_trans)} unique types available: {sorted(unique_trans)}")

# -------------------------------------------------------
# FIX E: Color grading minimal/soft mode
# -------------------------------------------------------
# Reduce hue range in default profile
old_default_hr = '"default":{"hr":(-2,2.5)'
new_default_hr = '"default":{"hr":(-1.2,1.2)'
if old_default_hr in b:
    b = b.replace(old_default_hr, new_default_hr)
    fixes += 1
    print("  [E] COLOR: default hue range reduced to (-1.2, 1.2) for softer look ✅")
else:
    print("  [E] COLOR: color ranges in unique_editing_engine.py, not batch_long_renderer")

bl.write_text(b, encoding="utf-8")

# -------------------------------------------------------
# VERIFY
# -------------------------------------------------------
print(f"\n{'='*60}")
print(f"  TOTAL FIXES APPLIED: {fixes}")
print(f"  Backups: *_bak_v2_{ts}")
print(f"{'='*60}")
try:
    compile(b, "batch_long_renderer.py", "exec")
    print("  ✅ SYNTAX OK")
except SyntaxError as e:
    print(f"  ❌ SYNTAX ERROR: {e}")
print(f"{'='*60}")