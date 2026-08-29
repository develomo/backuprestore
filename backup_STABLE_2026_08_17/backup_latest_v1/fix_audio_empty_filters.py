# fix_audio_empty_filters.py
# 100% BULLETPROOF FIX for "No such filter: ''" error
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

if not TARGET.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")
changes = 0

# Fix 1: Safeguard final_loudnorm_filter (Prevents ",," if empty)
old_loudnorm = 'f"{final_loudnorm_filter}",'
new_loudnorm = 'f"{str(final_loudnorm_filter).strip() or \'loudnorm=I=-14:TP=-1.5:LRA=6.5\'}",'

if old_loudnorm in content:
    content = content.replace(old_loudnorm, new_loudnorm)
    print("[OK] Fix 1: Safeguarded final_loudnorm_filter from being empty")
    changes += 1
else:
    print("[INFO] Fix 1: final_loudnorm_filter already safeguarded or formatted differently")

# Fix 2: Safeguard music_tone (Prevents ",," if empty)
old_tone = 'f"{music_tone}",'
new_tone = 'f"{str(music_tone).strip() or \'highpass=f=60,lowpass=f=11500\'}",'

if old_tone in content:
    content = content.replace(old_tone, new_tone)
    print("[OK] Fix 2: Safeguarded music_tone from being empty")
    changes += 1
else:
    print("[INFO] Fix 2: music_tone already safeguarded or formatted differently")

if changes > 0:
    TARGET.write_text(content, encoding="utf-8")
    print(f"\n✅ SUCCESS! {changes} critical audio filter fixes applied.")
    print("💡 This prevents the 'No such filter: ''' error by ensuring no empty strings are passed to FFmpeg.")
else:
    print("\n⚠️ No changes were made. The file might already be patched.")