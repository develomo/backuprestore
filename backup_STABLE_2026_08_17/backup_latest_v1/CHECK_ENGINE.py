import sys, os
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")

print("=" * 70)
print("  ENGINE DIAGNOSTIC")
print("=" * 70)

print("\n[1] Finding ALL unique_editing_engine.py files...")
for root, dirs, files in os.walk(str(BASE)):
    for f in files:
        if f == "unique_editing_engine.py":
            p = Path(root) / f
            size = p.stat().st_size
            with open(p) as fh:
                first = fh.readline().strip()
            print(f"  {p}  ({size:,} bytes)  first: {first[:80]}")

print("\n[2] Testing get_clip_dna...")
sys.path.insert(0, str(BASE))
from unique_editing_engine import get_clip_dna, pick_motion

clips_dir = BASE / "clips"
clip_files = sorted(clips_dir.glob("*.mp4"))
if clip_files:
    test_clip = str(clip_files[0])
    print(f"  Test clip: {test_clip}")
    dna = get_clip_dna(test_clip, 0, 'default', 150)
    print(f"  Keys: {list(dna.keys())}")
    print(f"  motion_name: {repr(dna.get('motion_name'))}")
    print(f"  color_params: {dna.get('color_params')}")
    print(f"  use_grain: {dna.get('use_grain')}, use_blur: {dna.get('use_blur')}")
    
    print("\n  Testing NON-EXISTENT path...")
    dna2 = get_clip_dna("NONEXISTENT.mp4", 99, 'default', 150)
    print(f"  motion_name: {repr(dna2.get('motion_name'))}")
else:
    print("  No clips found!")

print("\n[3] Testing pick_motion...")
name, filt = pick_motion('default', 0)
print(f"  pick_motion('default', 0) = name: {repr(name)}")
name2, filt2 = pick_motion('default', 999999)
print(f"  pick_motion('default', 999999) = name: {repr(name2)}")

print("\n[4] Checking render_clip_segment...")
from batch_long_renderer import render_clip_segment, ENGINES_AVAILABLE
print(f"  ENGINES_AVAILABLE: {ENGINES_AVAILABLE}")
import inspect
src = inspect.getsource(render_clip_segment)
for line in src.split('\n')[:25]:
    print(f"  | {line}")
print("\n" + "=" * 70)