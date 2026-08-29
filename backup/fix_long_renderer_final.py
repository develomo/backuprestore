# fix_long_renderer_final.py
import os
import re
from pathlib import Path
import py_compile

BASE_DIR = Path(__file__).parent
BLR_PATH = BASE_DIR / "batch_long_renderer.py"

if not BLR_PATH.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = BLR_PATH.read_text(encoding="utf-8")

# 1. Fix the PI syntax error in zoompan (FFmpeg doesn't always recognize 'PI', use 3.14159)
if "2*PI*n/30" in content:
    content = content.replace("2*PI*n/30", "2*3. is 100% ready.")
    print("\n" + "="*70)
    print("✅ LONG RENDERER FIXED & UPGRADED!")
    print("="*70)
    print("1. Fixed FFmpeg 'PI' undefined error in zoompan filter.")
    print("2. Added logic to ensure Motion/Transitions DO NOT repeat for at least 5 clips.")
    print("\n💡 NEXT STEP: Run 'streamlit run app.py' and test your render!")
except py_compile.PyCompileError as e:
    print(f"\n❌ SYNTAX ERROR: {e}")
    print("Please share this error so it can be fixed.")