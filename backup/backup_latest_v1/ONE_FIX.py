import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

print("=" * 70)
print("  ONE FIX — 3 targeted line edits")
print("=" * 70)

bl = BASE / "batch_long_renderer.py"
shutil.copy2(bl, BASE / f"batch_long_renderer.py.bak_onefix_{ts}")
b = bl.read_text(encoding="utf-8")
fixes = 0

# --- FIX 1: Motion fallback ---
# Line: mn = str(dna.get('motion_name', '?'))
# To:   mn = str(dna.get('motion_name') or 'default_push')
old1 = "mn = str(dna.get('motion_name', '?'))"
new1 = "mn = str(dna.get('motion_name') or 'default_push')"
if old1 in b:
    b = b.replace(old1, new1)
    fixes += 1
    print("  [1] Motion fallback ✅")
else:
    print("  [1] Motion line not found")

# --- FIX 2: XFADE unstable types ---
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
    print(f"  [2] XFADE: {cnt} types fixed ✅")
else:
    print("  [2] XFADE: already clean")

# --- FIX 3: Exception traceback ---
old3 = "log(_tb2.format_exc()[-300:])"
new3 = "log('[EngineDNA] TRACEBACK:\\n' + _tb2.format_exc())"
if old3 in b:
    b = b.replace(old3, new3)
    fixes += 1
    print("  [3] Full traceback ✅")
else:
    print("  [3] Traceback line not found")

bl.write_text(b, encoding="utf-8")

print(f"\nFIXES: {fixes}/3")
try:
    compile(b, "batch_long_renderer.py", "exec")
    print("✅ SYNTAX OK")
except SyntaxError as e:
    print(f"❌ SYNTAX: {e}")
print(f"Backup: *_bak_onefix_{ts}")