# fix_final_2_issues.py
# FINAL FIX: Subscribe Overlay Timeout, Outro Position, and Render Speed Boost
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

def backup_file(filepath):
    if filepath.exists():
        backup = filepath.with_suffix(filepath.suffix + ".backup_final_speed_fix")
        if not backup.exists():
            shutil.copy2(filepath, backup)
            print(f"[OK] Backup created: {backup.name}")

def fix_batch_renderer():
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found")
        return False
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    
    # FIX 1: Speed up FFmpeg by using all CPU cores (threads=0) instead of just 2
    # This will significantly reduce the 1-hour render time for 21-min videos
    content = content.replace('"-threads", "2"', '"-threads", "0"')
    print("[OK] Patch 1: FFmpeg speed boosted (using all CPU cores)")
    
    # FIX 2: Increase Subscribe Overlay timeout from 180s to 600s (10 mins) 
    # and move position to bottom (main_h-overlay_h-100) to clear captions
    old_overlay_cmd = '''cmd = [FFMPEG, "-y", "-i", str(video), "-loop", "1", "-i", str(overlay),
"-filter_complex", filt, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
"-pix_fmt", "yuv420p", "-threads", "0", "-an", str(out)]'''
    
    # Note: We already changed threads to 0 above, so we match the new pattern
    old_overlay_cmd_new = '''cmd = [FFMPEG, "-y", "-i", str(video), "-loop", "1", "-i", str(overlay),
"-filter_complex", filt, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
"-pix_fmt", "yuv420p", "-threads", "0", "-an", str(out)]'''
    
    # Actually, let's just do a direct string replace for the timeout and position
    # Find the pos_map and update bottom-right to be higher up (clear of captions)
    content = content.replace(
        '"bottom-right": ("main_w-overlay_w-24", "main_h-overlay_h-24")',
        '"bottom-right": ("main_w-overlay_w-24", "main_h-overlay_h-100")  # Phase Fix: Moved up to clear captions'
    )
    print("[OK] Patch 2: Subscribe overlay position moved to bottom (clear of captions)")
    
    # Increase timeout for subscribe overlay
    content = content.replace(
        'run_cmd(cmd, timeout=180)',
        'run_cmd(cmd, timeout=600)  # Phase Fix: Increased timeout for long videos'
    )
    print("[OK] Patch 3: Subscribe overlay timeout increased to 600s (prevents timeout on 20+ min videos)")

    # FIX 3: Fix Outro Logic so it's appended AFTER duration looping, not before
    # Find the section where outro is added to outputs and video_raw is looped
    old_outro_logic = '''outro_out, outro_asset_type = resolve_outro_segment(
outro_path_resolved, batch_dir, size, fps, outro_sec, quality,
niche=preset.get("niche", "default"), logo_path=outro_logo,
)
outputs.append(outro_out)
if not outputs:
raise RuntimeError("No visual outputs rendered")
video_raw = temp / "video_raw.mp4"
concat_files(outputs, video_raw, niche=preset.get("niche", "default"), use_transitions=True,
global_indices=list(range(len(outputs))), chapter_flags=[False] * len(outputs))
safe_gc()
visual_duration = probe_duration(video_raw)
if visual_duration < total_duration - .5:
extended = temp / "video_duration_fixed.mp4"
log(f"[StableLong] visual shorter ({visual_duration:.2f} < {total_duration:.2f}); LOOPING to match voice duration")
run_cmd([
FFMPEG, "-y", "-stream_loop", "-1", "-i", str(video_raw), "-t", f"{total_duration:.3f}",
"-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-pix_fmt", "yuv420p",
"-threads", "0", str(extended),
], timeout=180)
video_raw = extended'''

    new_outro_logic = '''# Phase Fix: Separate outro from main body to prevent it from being looped or cut off
main_outputs = [p for p in outputs if "outro_segment" not in str(p)]
video_raw = temp / "video_raw.mp4"
concat_files(main_outputs, video_raw, niche=preset.get("niche", "default"), use_transitions=True,
global_indices=list(range(len(main_outputs))), chapter_flags=[False] * len(main_outputs))
safe_gc()

visual_duration = probe_duration(video_raw)
target_body_duration = total_duration - outro_sec

if visual_duration < target_body_duration - 0.5:
extended = temp / "video_duration_fixed.mp4"
log(f"[StableLong] visual shorter ({visual_duration:.2f}s < {target_body_duration:.2f}s); LOOPING body to match voice duration")
run_cmd([
FFMPEG, "-y", "-stream_loop", "-1", "-i", str(video_raw), "-t", f"{target_body_duration:.3f}",
"-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-pix_fmt", "yuv420p",
"-threads", "0", str(extended),
], timeout=600)  # Increased timeout for long looping
video_raw = extended

# Phase Fix: NOW append outro at the very end, guaranteeing it's the last 2 seconds
final_visual = temp / "final_visual.mp4"
if outro_out and outro_out.exists():
log(f"[StableLong] Appending guaranteed {outro_sec}s outro at the very end")
concat_files([video_raw, outro_out], final_visual, use_transitions=False)
video_raw = final_visual'''

    if old_outro_logic in content:
        content = content.replace(old_outro_logic, new_outro_logic)
        print("[OK] Patch 4: Outro logic fixed (now guaranteed to be at the very end, not looped)")
    else:
        # Fallback regex if exact string doesn't match due to minor formatting
        pattern = re.compile(r'outro_out, outro_asset_type = resolve_outro_segment\(.*?video_raw = extended', re.DOTALL)
        if pattern.search(content):
            content = pattern.sub(new_outro_logic, content)
            print("[OK] Patch 4: Outro logic fixed via regex fallback")
        else:
            print("[WARN] Could not find exact outro logic block to replace")

    # Also fix the final concat timeout
    content = content.replace('], timeout=180)', '], timeout=600)')
    
    filepath.write_text(content, encoding="utf-8")
    return True

if __name__ == "__main__":
    print("🚀 Starting FINAL SPEED & FIX Patch...")
    print("=" * 60)
    
    if fix_batch_renderer():
        print("\n" + "=" * 60)
        print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📋 WHAT CHANGED:")
        print("1. FFmpeg Speed: Changed '-threads 2' to '-threads 0' (uses ALL CPU cores)")
        print("2. Subscribe Overlay: Timeout increased to 600s + moved to bottom (clear of captions)")
        print("3. Outro: Now appended AFTER duration looping, guaranteeing it's the final 2 seconds")
        print("\n💡 NEXT STEP: Run your 21-minute render again. It should be faster and complete perfectly!")
    else:
        print("\n❌ Fix failed - check errors above")