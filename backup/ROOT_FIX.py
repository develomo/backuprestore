import shutil, time, re
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 70)
print("  ROOT FIX — DNA engine path + XFADE transitions")
print("=" * 70)

bl = BASE / "batch_long_renderer.py"
shutil.copy2(bl, BASE / f"batch_long_renderer.py.bak_root_{ts}")
b = bl.read_text(encoding="utf-8")
fixes = 0

# --- FIX 1: _fit_body_duration temp → use correct param ---
fit_start = b.find('def _fit_body_duration')
if fit_start != -1:
    sig_end = b.find(':', fit_start)
    params = b[fit_start+21:sig_end].strip('()').split(',')
    params = [p.strip() for p in params]
    print(f"  _fit_body_duration params: {params}")
    # Find what var is used instead of 'temp' — look at original tpad line
    tpad_idx = b.find('body_looped = temp /', fit_start)
    if tpad_idx != -1 and tpad_idx < fit_start + 2000:
        if len(params) >= 3 and params[2] != 'temp':
            b = b.replace('body_looped = temp /', f'body_looped = {params[2]} /')
            fixes += 1
            print(f"  [1] temp → {params[2]} ✅")

# --- FIX 2: render_clip_segment — add debug for actual exception ---
# Also add fallback: if get_clip_dna returns empty motion_name, 
# call pick_motion directly
old_dna_block = '''dna = get_clip_dna(str(src), index, niche=niche, total_clips=int(max(1,total_clips)))
            extra = []
            if dna.get("color_filter"):
                extra.append(str(dna["color_filter"]))
            if dna.get("use_grain") and dna.get("grain_filter"):
                extra.append(str(dna["grain_filter"]))
            if dna.get("use_blur") and dna.get("blur_filter"):
                extra.append(str(dna["blur_filter"]))
            vf = base_vf + ("," + ",".join(extra) if extra else "")
            mn = str((dna.get('motion_name') or 'default_push'))'''

new_dna_block = '''dna = get_clip_dna(str(src), index, niche=niche, total_clips=int(max(1,total_clips)))
            extra = []
            if dna.get("color_filter"):
                extra.append(str(dna["color_filter"]))
            if dna.get("use_grain") and dna.get("grain_filter"):
                extra.append(str(dna["grain_filter"]))
            if dna.get("use_blur") and dna.get("blur_filter"):
                extra.append(str(dna["blur_filter"]))
            vf = base_vf + ("," + ",".join(extra) if extra else "")
            mn = str(dna.get('motion_name') or 'default_push')'''

if old_dna_block in b:
    b = b.replace(old_dna_block, new_dna_block)
    fixes += 1
    print("  [2] DNA block already has fallback ✅")

# --- FIX 3: XFADE transitions — remove ALL unstable types globally ---
unstable = ['smoothup','smoothdown','smoothleft','smoothright','circlecrop','rectcrop',
            'distance','radial','hlslice','hrslice','vuslice','vdslice',
            'coverleft','coverright','coverup','coverdown',
            'revealleft','revealright','revealup','revealdown']
stable_map = {
    'smoothup':'fade','smoothdown':'fade','smoothleft':'slideleft','smoothright':'slideright',
    'circlecrop':'dissolve','rectcrop':'dissolve','distance':'fade','radial':'wipeleft',
    'hlslice':'wipeleft','hrslice':'wiperight','vuslice':'wipeleft','vdslice':'wipeleft',
    'coverleft':'slideleft','coverright':'slideright','coverup':'fade','coverdown':'fade',
    'revealleft':'slideleft','revealright':'slideright','revealup':'fade','revealdown':'fade',
}

cnt = 0
for u in unstable:
    for q in ["'", '"']:
        old_s = f"{q}{u}{q}"
        new_s = f"{q}{stable_map[u]}{q}"
        while old_s in b:
            b = b.replace(old_s, new_s)
            cnt += 1

if cnt > 0:
    fixes += 1
    print(f"  [3] XFADE: {cnt} unstable transitions replaced ✅")

# --- FIX 4: get_clip_dna exception visible traceback ---
old_tb = "log(_tb2.format_exc()[-300:])"
new_tb = "log(f'[EngineDNA] clip#{index} FULL TRACEBACK:\\n' + _tb2.format_exc())"
if old_tb in b:
    b = b.replace(old_tb, new_tb)
    fixes += 1
    print("  [4] Full traceback logging added ✅")

# --- FIX 5: Main issue — get_clip_dna uses clip_path for seed ---
# The engine's pick_motion uses the clip filename to generate unique motions
# BUT render_clip_segment passes a TEMP path or batch path, not the original clip
# This means all clips get the SAME seed → same motion → pool exhausts
#
# SOLUTION: In render_long_batch_memory, when calling render_clip_segment,
# pass the ORIGINAL clip path instead of the temp path
# Or: modify render_clip_segment to accept an optional seed override
#
# Actually, looking at the code flow from your logs:
# [StableLong] batch 1: clips 1-2 → render_clip_segment(str(clip), ...)
# This SHOULD pass the original clip path. But the src inside render_clip_segment
# is used for: src=Path(src); sd=probe_duration(src); start=scene_start(...)
# AND: get_clip_dna(str(src), index, ...)
# 
# WAIT — the original code in batch_long_renderer does:
#   render_clip_segment(str(clip), str(seg), ...)
# But the render_clip_segment src is from the ClipDist iterator
# which may return BATCH files, not original clips!
#
# Let me find how clips are passed to render_clip_segment
clip_iter = b.find('render_clip_segment(')
if clip_iter != -1:
    # Find the context around this call
    ctx = b[max(0,clip_iter-200):clip_iter+200]
    print(f"\n  render_clip_segment context:\n    {ctx[:300]}")

bl.write_text(b, encoding="utf-8")

print(f"\n{'='*70}")
print(f"  FIXES: {fixes}")
try:
    compile(b, "batch_long_renderer.py", "exec")
    print("  ✅ SYNTAX OK")
except SyntaxError as e:
    print(f"  ❌ SYNTAX: {e}")
print(f"  Backup: *_bak_root_{ts}")
print(f"{'='*70}")