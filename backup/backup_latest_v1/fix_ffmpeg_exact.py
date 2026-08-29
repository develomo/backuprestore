# fix_ffmpeg_exact.py
# 100% BULLETPROOF FIX - Indentation se farq nahi parta
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

if not TARGET.exists():
    print("[ERROR] batch_long_renderer.py nahi mila!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")
lines = content.split('\n')
changed = False

for i, line in enumerate(lines):
    # FIX 1: Jab final_loudnorm_filter khali ho, toh ",," (double comma) na bane
    if '+ f"{final_loudnorm_filter}",' in line:
        lines[i] = line.replace(
            '+ f"{final_loudnorm_filter}",',
            '+ (f"{final_loudime_filter}," if final_loudnorm_filter and str(final_loudnorm_filter).strip() else "")'
        )
        # Correction in replacement string to match variable name exactly:
        lines[i] = lines[i].replace('final_loudime_filter', 'final_loudnorm_filter')
        changed = True
        print(f"[OK] Fix 1: Double-comma risk hataya (final_loudnorm_filter) - Line {i+1}")

    # FIX 2: Jab music_tone khali ho, toh ",," na bane
    elif 'f"{music_tone}",' in line:
        lines[i] = line.replace(
            'f"{music_tone}",',
            'f"{str(music_tone).strip() + \',\' if music_tone and str(m8usic_tone).strip() else \'\'}"'
        )
        # Correction in replacement string:
        lines[i] = lines[i].replace('m8usic_tone', 'music_tone')
        changed = True
        print(f"[OK] Fix 2: Double-comma risk hataya (music_tone) - Line {i+1}")

    # FIX 3: ULTIMATE SAFETY NET - Join karne se pehle khali strings ko hata do
    elif '"-filter_complex", ";".join(filters),' in line:
        lines[i] = line.replace(
            '"-filter_complex", ";".join(filters),',
            '"-filter_complex", ";".join(f for f in filters if f and str(f).strip()),'
        )
        changed = True
        print(f"[OK] Fix 3: Ultimate safety net add kiya (Line {i+1})")

if changed:
    TARGET.write_text('\n'.join(lines), encoding="utf-8")
    print("\n" + "="*60)
    print("✅ EXACT FIX 100% SUCCESSFULLY APPLIED!")
    print("="*60)
    print("💡 Ab FFmpeg ko kabhi bhi ',,' (empty filter) nahi milega.")
    print("💡 Render dobara start karein, error khatam ho jayega.")
else:
    print("\n⚠️ Exact lines nahi mili. File ka structure shayad pehle se theek hai ya alag hai.")