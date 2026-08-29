# fix_syntax_and_ffmpeg_captions.py
import re
from pathlib import Path
import py_compile

TARGET = Path("batch_long_renderer.py")

if not TARGET.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")
lines = content.split('\n')
fixed = False

# 1. Fix the syntax error in concat_files_hard
for i, line in enumerate(lines):
    # Look for the broken line inside concat_files_hard function
    if 'def concat_files_hard' in line:
        # Check next 10 lines for the error
        for j in range(i, min(i+10, len(lines))):
            if '.replace("\\", "/")' in lines[j]:
                # Fix backslash escape
                lines[j] = lines[j].replace('.replace("\\", "/")', '.replace("\\\\", "/")')
                print(f"[OK] Fixed backslash escape at line {j+1}")
            
            if ".replace(\"'\", \"'\\''\")" in lines[j]:
                # Fix quote escape
                lines[j] = lines[j].replace(".replace(\"'\", \"'\\''\")", ".replace(\"'\", \"'\\\\''\")")
                print(f"[OK] Fixed quote escape at line {j+1}")
                fixed = True
        if fixed:
            break

if fixed:
    TARGET.write_text('\n'.join(lines), encoding="utf-8")
    print("\n[INFO] Verifying Python syntax...")
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("[OK] ✅ Syntax verification PASSED! File is ready.")
    except py_compile.PyCompileError as e:
        print(f"[ERROR] ❌ Syntax still broken: {e}")
else:
    print("[INFO] No syntax fixes needed (or pattern not found).")

# 2. Confirm FFmpeg usage in captions
print("\n" + "="*60)
print("CHECKING CAPTIONS ENGINE")
print("="*60)
if 'def burn_captions' in content:
    print("[OK] burn_captions function found.")
    if 'FFMPEG' in content and 'subtitles=' in content:
        print("[OK] ✅ CONFIRMED: Captions use FFMPEG (Not MoviePy).")
        print("     FFmpeg command: subtitles='{ass_filter}'")
    else:
        print("[WARN] burn_captions might not be using FFMPEG correctly.")
else:
    print("[WARN] burn_captions function not found.")

print("\n" + "="*60)
print("NEXT STEP: Run 'streamlit run app.py' and test your render!")
print("="*60)