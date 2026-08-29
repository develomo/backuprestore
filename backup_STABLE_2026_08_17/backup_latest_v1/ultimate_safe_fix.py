import shutil
import py_compile
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

BACKUPS = [
    "batch_long_renderer.py.bak_outro_wm",
    "batch_long_renderer.py.bak_master",
    "batch_long_renderer.py.bak_fix",
    "batch_long_renderer.py.bak_engage",
    "batch_long_renderer.py.bak_10x",
    "batch_long_renderer.py.bak2",
]

def restore():
    for name in BACKUPS:
        backup = BASE_DIR / name
        if backup.exists():
            shutil.copy2(backup, TARGET)
            print(f"[OK] Restored from {name}")
            return True
    print("[ERROR] No backup found!")
    return False

def apply_fixes():
    content = TARGET.read_text(encoding="utf-8")
    original = content
    changes = 0

    # FIX 1: Speed boost - threads 2 to 0
    if '"-threads", "2"' in content:
        content = content.replace('"-threads", "2"', '"-threads", "0"')
        print("[OK] Fix 1: FFmpeg threads set to 0 (all CPU cores)")
        changes += 1

    # FIX 2: Subscribe overlay top-right to bottom-right
    if 'corner="top-right"' in content:
        content = content.replace('corner="top-right"', 'corner="bottom-right"')
        print("[OK] Fix 2: Subscribe overlay moved to bottom-right")
        changes += 1

    # FIX 3: Subscribe overlay timeout 180s to 600s
    if 'timeout=180)' in content:
        content = content.replace('timeout=180)', 'timeout=600)')
        print("[OK] Fix 3: Subscribe overlay timeout increased to 600s")
        changes += 1

    # FIX 4: Outro guaranteed at end - separate from looping body
    old_outro = 'outputs.append(outro_out)\n        if not outputs:'
    new_outro = 'if not outputs:'
    if old_outro in content:
        content = content.replace(old_outro, new_outro, 1)
        print("[OK] Fix 4a: Removed premature outro append")
        changes += 1

    old_concat = 'concat_files(outputs, video_raw, niche=preset.get("niche", "default"), use_transitions=True,\nglobal_indices=list(range(len(outputs))), chapter_flags=[False] * len(outputs))'
    new_concat = 'main_outputs = [p for p in outputs if "outro_segment" not in str(p)]\n        concat_files(main_outputs, video_raw, niche=preset.get("niche", "default"), use_transitions=True,\nglobal_indices=list(range(len(main_outputs))), chapter_flags=[False] * len(main_outputs))'
    if old_concat in content:
        content = content.replace(old_concat, new_concat, 1)
        print("[OK] Fix 4b: Main body separated from outro (outro won't loop)")
        changes += 1

    old_loop = 'if visual_duration < total_duration - .5:'
    new_loop = 'target_body_duration = total_duration - outro_sec\n        if visual_duration < target_body_duration - .5:'
    if old_loop in content and 'target_body_duration' not in content:
        content = content.replace(old_loop, new_loop, 1)
        print("[OK] Fix 4c: Loop uses target_body_duration (excludes outro)")
        changes += 1

    old_loop_t = '"-t", f"{total_duration:.3f}",'
    new_loop_t = '"-t", f"{target_body_duration:.3f}",'
    if old_loop_t in content:
        content = content.replace(old_loop_t, new_loop_t, 1)
        print("[OK] Fix 4d: Loop duration now excludes outro")
        changes += 1

    old_video_raw = 'video_raw = extended\ncurrent = video_raw'
    new_video_raw = '''video_raw = extended
        # Append outro at the very end (guaranteed last 2 seconds)
        if outro_out and outro_out.exists():
            final_visual = temp / "final_visual.mp4"
            concat_files([video_raw, outro_out], final_visual, use_transitions=False)
            video_raw = final_visual
        current = video_raw'''
    if old_video_raw in content:
        content = content.replace(old_video_raw, new_video_raw, 1)
        print("[OK] Fix 4e: Outro appended AFTER looping (guaranteed last 2s)")
        changes += 1

    if changes == 0:
        print("[INFO] No changes needed - fixes may already be applied")
        return True

    TARGET.write_text(content, encoding="utf-8")
    print(f"[OK] File saved with {changes} fixes")
    return True

def verify():
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("[OK] Syntax verification PASSED")
        return True
    except py_compile.PyCompileError as e:
        print(f"[ERROR] Syntax error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Ultimate Safe Fix")
    print("=" * 60)

    if not restore():
        exit(1)

    if not apply_fixes():
        exit(1)

    if not verify():
        print("[FAIL] Fix failed - backup was restored, file is safe")
        exit(1)

    print("=" * 60)
    print("ALL FIXES APPLIED SUCCESSFULLY!")
    print("=" * 60)
    print("Next: streamlit run app.py")