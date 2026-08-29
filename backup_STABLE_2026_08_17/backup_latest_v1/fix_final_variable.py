# fix_final_variable.py
# Simple Fix: Restores 'final = ' to the render call
from pathlib import Path
import re

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "safe_long_video_polished.py"

if not TARGET.exists():
    print("[ERROR] safe_long_video_polished.py not found!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")
lines = content.split('\n')
fixed = False

# Find the exact line and add 'final = ' to it
for i, line in enumerate(lines):
    # We look for the line that calls render_long_batch_memory but doesn't have 'final = '
    if line.strip().startswith("render_long_batch_memory(") and "clip_paths=clip_list" in line:
        if "final = " not in line:
            # Preserve original indentation
            indent = len(line) - len(line.lstrip())
            lines[i] = " " * indent + "final = " + line.lstrip()
            fixed = True
            print(f"[OK] Fix Applied: Added 'final = ' at line {i+1}")
            break

if fixed:
    TARGET.write_text('\n'.join(lines), encoding="utf-8")
    print("\n✅ SUCCESS! The 'final' variable error is now fixed.")
    print("💡 Ab aap dobara render karein, video banegi aur koi error nahi aayega.")
else:
    print("\n[INFO] Line already fixed or not found.")