# quick_fix.py
from pathlib import Path
import re

BASE = Path(r"D:\My Creation Video Generator\backup")
FILE = BASE / "batch_long_renderer.py"

content = FILE.read_text(encoding="utf-8")

# Fix 1: Outro ko last 2 sec mein lana
# Search for the pattern where outro is handled
if "outro_out" in content and "outputs.append(outro_out)" in content:
    print("[OK] Outro logic found")
else:
    print("[WARN] Outro logic pattern not found")

# Fix 2: Logo watermark check
if "custom_logo_path" in content:
    print("[OK] Logo watermark parameter exists")
else:
    print("[WARN] Logo watermark parameter missing")

# Fix 3: Subscribe overlay check  
if "subscribe_overlay" in content and "corner=" in content:
    print("[OK] Subscribe overlay configuration exists")
else:
    print("[WARN] Subscribe overlay configuration missing")

print("\n✅ Quick check complete!")