# fix_audio_simple.py
# Simple & Safe Fix - Only targets the exact 2 substrings causing the error
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

if not TARGET.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")

# Fix 1: Safeguard music_tone
old1 = 'f"{music_tone}",'
new1 = 'f"{str(music_tone).strip() + \',\' if str(music_tone).strip() else \'\'}",'
if old1 in content:
    content = content.replace(old1, new1)
    print("[OK] Fix 1: music_tone safeguarded (prevents empty comma)")

# Fix 2: Safeguard final_loudnorm_filter
old2 = 'f"{final_loudnorm_filter}",'
new2 = 'f"{str(final_loudnorm_filter).strip() + \',\' if str(final_loudnorm_filter).strip() else \'\'}",'
if old2 in content:
    content = content.replace(old2, new2)
    print("[OK] Fix 2: final_loudnorm_filter safeguarded (prevents empty comma)")

TARGET.write_text(content, encoding="utf-8")
print("\n✅ DONE! Script complete. Ab aap render start kar sakte hain.")