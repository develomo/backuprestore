import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 70)
print("  FIX ALL ONCE — 4 fixes, no block replacement")
print("=" * 70)

bl = BASE / "batch_long_renderer.py"
shutil.copy2(bl, BASE / f"batch_long_renderer.py.bak_finalfix_{ts}")
b = bl.read_text(encoding="utf-8")
fixes = 0

# --- FIX 1: clip_paths → clips ---
if 'clip_paths' in b:
    b = b.replace('clip_paths', 'clips')
    fixes += 1
    print("  [1] clip_paths → clips ✅")

# --- FIX 2: Motion fallback ---
old2 = "mn = str(dna.get('motion_name', '?'))"
new2 = "mn = str(dna.get('motion_name') or 'default_push')"
if old2 in b:
    b = b.replace(old2, new2)
    fixes += 1
    print("  [2] Motion fallback ✅")

# --- FIX 3: XFADE unstable types ---
unstable_map = {
    'smoothup':'fade','smoothdown':'fade','smoothleft':'slideleft','smoothright':'slideright',
    'circlecrop':'dissolve','rectcrop':'dissolve','distance':'fade','radial':'wipeleft',
    'hlslice':'wipeleft','hrslice':'wiperight','vuslice':'wipeleft','vdslice':'wipeleft',
    'coverleft':'slideleft','coverright':'slideright','coverup':'fade','coverdown':'fade',
    'revealleft':'slideleft','revealright':'slideright','revealup':'fade','revealdown':'fade',
}
cnt = 0
for u, s in unstable_map.items():
    for q in ["'", '"']:
        o = f"{q}{u}{q}"
        n = f"{q}{s}{q}"
        while o in b:
            b = b.replace(o, n)
            cnt += 1
if cnt:
    fixes += 1
    print(f"  [3] XFADE: {cnt} types fixed ✅")

# --- FIX 4: Music aloop ---
if 'if music and Path(music).exists():' in b and 'aloop' not in b:
    b = b.replace(
        'atrim=0:{body_len:.3f}',
        'aloop=loop=-1:size=2e9,atrim=0:{body_len:.3f}'
    )
    fixes += 1
    print("  [4] Music aloop ✅")

bl.write_text(b, encoding="utf-8")

print(f"\n{'='*70}")
print(f"  FIXES: {fixes}/4")
try:
    compile(b, "batch_long_renderer.py", "exec")
    print("  ✅ SYNTAX OK")
except SyntaxError as e:
    print(f"  ❌ SYNTAX: {e}")
print(f"  Backup: *_bak_finalfix_{ts}")
print(f"{'='*70}")