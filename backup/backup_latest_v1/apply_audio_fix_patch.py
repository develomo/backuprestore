"""
AUDIO FIX PATCH FOR master_pipeline.py
=======================================
Ye script aapke master_pipeline.py file mein 3 critical changes
automatically apply karegi:

1. build_audio_for_pipeline() mein .wav -> .m4a
2. build_integrated_audio_for_pipeline() mein .wav -> .m4a
3. export_final_pipeline_video() mein duration probe fix

Usage:
    python apply_audio_fix_patch.py
"""
import re
from pathlib import Path

MASTER_PIPELINE = Path(__file__).parent / "master_pipeline.py"

if not MASTER_PIPELINE.exists():
    print(f"[ERROR] master_pipeline.py not found at: {MASTER_PIPELINE}")
    input("Press Enter to exit...")
    exit(1)

print(f"[INFO] Reading: {MASTER_PIPELINE}")
original_code = MASTER_PIPELINE.read_text(encoding="utf-8")
new_code = original_code
changes_made = 0

# ============================================================
# CHANGE 1: build_audio_for_pipeline() - .wav to .m4a
# ============================================================
old_pattern_1 = (
    'output_path=TEMP_DIR / f"audio_mix_{int(time.time())}.wav",'
)
new_pattern_1 = (
    'output_path=TEMP_DIR / f"audio_mix_{int(time.time())}.m4a",'  # FIX: .m4a for AAC codec
)

if old_pattern_1 in new_code:
    new_code = new_code.replace(old_pattern_1, new_pattern_1, 1)
    changes_made += 1
    print("[OK] Change 1 applied: build_audio_for_pipeline() .wav -> .m4a")
else:
    print("[WARN] Change 1: Pattern not found (may already be fixed)")

# ============================================================
# CHANGE 2: build_integrated_audio_for_pipeline() - .wav to .m4a
# ============================================================
old_pattern_2 = (
    'output_audio = TEMP_DIR / f"integrated_audio_mix_{int(time.time())}.wav"'
)
new_pattern_2 = (
    '# FIX: .m4a for AAC codec compatibility\n    output_audio = TEMP_DIR / f"integrated_audio_mix_{int(time.time())}.m4a"'
)

if old_pattern_2 in new_code:
    new_code = new_code.replace(old_pattern_2, new_pattern_2, 1)
    changes_made += 1
    print("[OK] Change 2 applied: build_integrated_audio_for_pipeline() .wav -> .m4a")
else:
    print("[WARN] Change 2: Pattern not found (may already be fixed)")

# ============================================================
# CHANGE 3: export_final_pipeline_video() - duration probe fix
# ============================================================
old_pattern_3 = (
    'duration=min(get_voice_duration_float(audio_path), get_voice_duration_float(audio_path)),'
)
new_pattern_3 = (
    'duration=get_voice_duration_float(audio_path),  # FIX: simplified duration probe'
)

if old_pattern_3 in new_code:
    new_code = new_code.replace(old_pattern_3, new_pattern_3, 1)
    changes_made += 1
    print("[OK] Change 3 applied: export_final_pipeline_video() duration fix")
else:
    print("[WARN] Change 3: Pattern not found (may already be fixed)")

# ============================================================
# SAVE THE PATCHED FILE
# ============================================================
if changes_made > 0:
    # Create backup first
    backup_path = MASTER_PIPELINE.with_suffix(".py.backup_before_audio_fix")
    backup_path.write_text(original_code, encoding="utf-8")
    print(f"\n[INFO] Backup created: {backup_path}")
    
    # Write patched file
    MASTER_PIPELINE.write_text(new_code, encoding="utf-8")
    print(f"[SUCCESS] {changes_made} change(s) applied to master_pipeline.py")
    print("[INFO] You can now run your Streamlit app. Audio should work correctly.")
else:
    print("\n[INFO] No changes needed. File may already be patched.")

print("\n[DONE] Patch complete!")
input("Press Enter to exit...")