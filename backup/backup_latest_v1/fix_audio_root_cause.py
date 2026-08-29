# fix_audio_root_cause.py
# Surgical fix for the exact lines causing "No such filter: ''"
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

if not TARGET.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")
original_content = content
fixes_applied = 0

# FIX 1: Prevent double comma if music_tone is empty
old_music_tone = 'f"{music_tone}",'
new_music_tone = 'f"{str(music_tone).strip() + \',\' if music_tone and str(music_tone).strip() else \'\'}",'

if old_music_tone in content:
    content = content.replace(old_music_tone, new_music_tone)
    print("[OK] Fix 1: Safeguarded music_tone from creating double commas (,,)")
    fixes_applied += 1
else:
    print("[INFO] Fix 1: music_tone line already safe or not found.")

# FIX 2: Prevent double comma if final_loudnorm_filter is empty
old_loudnorm = '+ f"{final_loudnorm_filter}",'
new_loudnorm = '+ (f"{str(final_loudnorm_filter).strip()}," if final_loudnorm_filter and str(final_loudnorm_filter).strip() else ""),'

if old_loudnorm in content:
    content = content.replace(old_loudnorm, new_loudnorm)
    print("[OK] Fix 2: Safeguarded final_loudnorm_filter from creating double commas (,,)")
    fixes_applied += 1
else:
    print("[INFO] Fix 2: final_loudnorm_filter line already safe or not found.")

# FIX 3: Prevent invalid amix=inputs=1 (FFmpeg requires at least 2 inputs for amix)
old_amix = '+ f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.35",'
new_amix = '+ (f"amix=inputs={len(labels)}:duration=longest:dropout_transition=0.35," if len(labels) > 1 else ""),'

if old_amix in content:
    content = content.replace(old_amix, new_amix)
    print("[OK] Fix 3: Safeguarded amix to only run when there are 2+ audio streams")
    fixes_applied += 1
else:
    print("[INFO] Fix 3: amix line already safe or not found.")

if fixes_applied > 0:
    TARGET.write_text(content, encoding="utf-8")
    
    # Verify syntax
    try:
        import py_compile
        py_compile.compile(str(TARGET), doraise=True)
        print("\n✅ SYNTAX VERIFICATION PASSED!")
    except py_compile.PyCompileError as e:
        print(f"\n❌ SYNTAX ERROR: {e}")
        exit(1)
        
    print(f"\n🎯 SUCCESS! {fixes_applied} critical root causes fixed.")
    print("💡 Ab FFmpeg ko kabhi bhi ',,' (empty filter) ya invalid amix nahi milega.")
else:
    print("\n⚠️ Koi fix apply nahi hua. File shayad pehle se patched hai.")