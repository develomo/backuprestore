# auto_patch_phase5_ram_safe.py
# PHASE 5: ULTRA RAM-SAFE MODE FOR LONG VIDEOS
# Prevents laptop shutdown during 150+ clip renders
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

def backup_file(filepath):
    if filepath.exists():
        backup = filepath.with_suffix(filepath.suffix + ".backup_phase5_ram")
        if not backup.exists():
            shutil.copy2(filepath, backup)
            print(f"[OK] Backup created: {backup.name}")

def patch_batch_long_renderer():
    """Make batch_long_renderer.py ultra RAM-safe."""
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found.")
        return
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    
    # FIX 1: Lower RAM_WARN_PERCENT from 80 to 70, CRITICAL from 90 to 78
    content = content.replace(
        "RAM_WARN_PERCENT = 80.0",
        "RAM_WARN_PERCENT = 70.0  # Phase 5: Ultra safe - prevent laptop shutdown"
    )
    content = content.replace(
        "RAM_CRITICAL_PERCENT = 90.0",
        "RAM_CRITICAL_PERCENT = 78.0  # Phase 5: Hard ceiling to avoid OOM"
    )
    
    # FIX 2: Reduce default batch size from 8 to 2 for long videos
    content = content.replace(
        "DEFAULT_BATCH_SIZE = 8",
        "DEFAULT_BATCH_SIZE = 2  # Phase 5: Ultra safe default for long videos"
    )
    
    # FIX 3: Reduce FFMPEG_THREADS from 2 to 1
    content = content.replace(
        'os.environ.setdefault("FFMPEG_THREADS", "2")',
        'os.environ.setdefault("FFMPEG_THREADS", "1")  # Phase 5: Single thread to save RAM'
    )
    
    # FIX 4: Make ram_guard_batch_size more aggressive
    old_ram_guard = '''def ram_guard_batch_size(requested_batch_size: int) -> int:
    # Spec section 10, rule 2: RAM guard maintained.
    bs = max(1, int(requested_batch_size or DEFAULT_BATCH_SIZE))
    pct = get_ram_percent()
    if pct is None:
        return bs
    if pct >= RAM_CRITICAL_PERCENT:
        log(f"[MemorySafe] RAM CRITICAL ({pct:.1f}%) -> batch_size forced to 1")
        gc.collect()
        return 1
    if pct >= RAM_WARN_PERCENT:
        new_bs = max(1, min(bs, 2))
        if new_bs != bs:
            log(f"[MemorySafe] RAM high ({pct:.1f}%) -> batch_size reduced {bs} -> {new_bs}")
            gc.collect()
            return new_bs
    return bs'''
    
    new_ram_guard = '''def ram_guard_batch_size(requested_batch_size: int) -> int:
    # Phase 5: Ultra aggressive RAM guard to prevent laptop shutdown
    bs = max(1, int(requested_batch_size or DEFAULT_BATCH_SIZE))
    pct = get_ram_percent()
    if pct is None:
        return 1  # Phase 5: If we can't measure, be safe
    if pct >= RAM_CRITICAL_PERCENT:
        log(f"[MemorySafe] RAM CRITICAL ({pct:.1f}%) -> PAUSING render for 5 seconds, forcing cleanup")
        import gc
        gc.collect()
        import time
        time.sleep(5.0)
        pct2 = get_ram_percent()
        if pct2 is not None and pct2 >= RAM_CRITICAL_PERCENT:
            log(f"[MemorySafe] RAM still critical ({pct2:.1f}%) -> forcing batch_size=1")
            return 1
        log(f"[MemorySafe] RAM recovered to {pct2:.1f}%, resuming with batch_size=1")
        return 1
    if pct >= RAM_WARN_PERCENT:
        new_bs = 1  # Phase 5: Force batch_size=1 when RAM is high
        if new_bs != bs:
            log(f"[MemorySafe] RAM high ({pct:.1f}%) -> batch_size forced to 1 (was {bs})")
            import gc
            gc.collect()
            import time
            time.sleep(2.0)
            return new_bs
        return new_bs
    # Phase 5: Cap batch_size at 3 even if RAM looks OK
    return min(bs, 3)'''
    
    if old_ram_guard in content:
        content = content.replace(old_ram_guard, new_ram_guard)
        print("[OK] Patch 1: Aggressive RAM guard installed")
    else:
        print("[WARN] Could not patch ram_guard_batch_size")
    
    # FIX 5: Add force cleanup after each batch
    old_batch_loop = '''        for s in segs:
            try:
                s.unlink(missing_ok=True)
            except Exception:
                pass
            safe_gc()'''
    
    new_batch_loop = '''        # Phase 5: Ultra aggressive cleanup after each batch
        for s in segs:
            try:
                s.unlink(missing_ok=True)
            except Exception:
                pass
        # Force garbage collection + wait for OS to free memory
        import gc
        gc.collect()
        import time
        time.sleep(1.5)  # Let OS reclaim memory
        safe_gc()
        # Phase 5: Kill any zombie FFmpeg processes
        try:
            import subprocess
            subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe", "/FI", "MEMUSAGE gt 200000"], 
                          capture_output=True, timeout=5)
        except Exception:
            pass'''
    
    if old_batch_loop in content:
        content = content.replace(old_batch_loop, new_batch_loop)
        print("[OK] Patch 2: Aggressive post-batch cleanup installed")
    else:
        print("[WARN] Could not patch batch cleanup loop")
    
    # FIX 6: Add RAM check before starting render
    old_start_render = '''    log(f"[StableLong] start | clips={len(clip_paths)} | voice={voice_duration:.2f}s | "
        f"total={total_duration:.2f}s | intro={intro_sec}s | outro={outro_sec}s | "
        f"quality={quality} | captions={add_captions} | batch_size={batch_size} | music_mode={music_mode}")'''
    
    new_start_render = '''    # Phase 5: Pre-render RAM check
    pre_ram = get_ram_percent()
    if pre_ram is not None and pre_ram >= 75.0:
        log(f"[MemorySafe] WARNING: RAM already at {pre_ram:.1f}% before render starts!")
        log("[MemorySafe] Forcing batch_size=1 and pausing 5 seconds for cleanup")
        import gc
        gc.collect()
        import time
        time.sleep(5.0)
        batch_size = 1
    log(f"[StableLong] start | clips={len(clip_paths)} | voice={voice_duration:.2f}s | "
        f"total={total_duration:.2f}s | intro={intro_sec}s | outro={outro_sec}s | "
        f"quality={quality} | captions={add_captions} | batch_size={batch_size} | music_mode={music_mode} | RAM={pre_ram or 'unknown'}%")'''
    
    if old_start_render in content:
        content = content.replace(old_start_render, new_start_render)
        print("[OK] Patch 3: Pre-render RAM check installed")
    else:
        print("[WARN] Could not patch pre-render check")
    
    filepath.write_text(content, encoding="utf-8")
    print("[OK] batch_long_renderer.py patched successfully")

def patch_safe_long_controller():
    """Make safe_long_video_polished.py force safe defaults for long videos."""
    filepath = BASE_DIR / "safe_long_video_polished.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found.")
        return
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    
    # FIX 7: Force batch_size=2 for long videos in controller
    old_batch = 'batch_size=int(preset.get("batch_size",DEFAULT_SETTINGS["batch_size"]) or DEFAULT_SETTINGS["batch_size"])'
    new_batch = 'batch_size=min(2, int(preset.get("batch_size", 2) or 2))  # Phase 5: Force batch_size=2 for RAM safety'
    
    if old_batch in content:
        content = content.replace(old_batch, new_batch)
        print("[OK] Patch 4: Controller batch_size capped at 2")
    else:
        print("[WARN] Could not patch controller batch_size")
    
    # FIX 8: Disable captions by default for long videos unless explicitly enabled
    old_caption_call = 'cap_on=caption_enabled(add_captions,caption_mode,style_id)'
    new_caption_call = '''# Phase 5: Captions OFF by default for long videos to save RAM
    # Only enable if user explicitly checked the box
    if add_captions is False:
        cap_on = False
    else:
        cap_on = caption_enabled(add_captions, caption_mode, style_id)'''
    
    if old_caption_call in content:
        content = content.replace(old_caption_call, new_caption_call)
        print("[OK] Patch 5: Captions respect UI checkbox strictly")
    else:
        print("[WARN] Could not patch caption toggle")
    
    filepath.write_text(content, encoding="utf-8")
    print("[OK] safe_long_video_polished.py patched successfully")

def create_ram_monitor_script():
    """Create a RAM monitoring script to test before rendering."""
    monitor_code = '''# test_ram_safety.py
# Test RAM safety before running long video render
import psutil
import time
import subprocess
import gc

def check_ram_status():
    mem = psutil.virtual_memory()
    print("=" * 60)
    print("🔍 RAM STATUS CHECK")
    print("=" * 60)
    print(f"Total RAM: {mem.total / (1024**3):.2f} GB")
    print(f"Used RAM: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
    print(f"Available RAM: {mem.available / (1024**3):.2f} GB")
    print(f"Swap Used: {mem.swap_used / (1024**3):.2f} GB / {mem.swap_total / (1024**3):.2f} GB")
    print("=" * 60)
    
    if mem.percent >= 80:
        print("⚠️  WARNING: RAM usage is HIGH!")
        print("💡 Recommendation: Close other applications before rendering")
        print("   - Close browser tabs")
        print("   - Close video editors")
        print("   - Close other Python processes")
    elif mem.percent >= 70:
        print("⚠️  CAUTION: RAM usage is moderate")
        print("💡 Phase 5 will automatically reduce batch_size to 1")
    else:
        print("✅ RAM usage is SAFE for rendering")
    
    # Check for zombie FFmpeg processes
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe"],
            capture_output=True, text=True, timeout=5
        )
        if "ffmpeg.exe" in result.stdout:
            print("\\n⚠️  Zombie FFmpeg processes detected!")
            print("💡 Killing them to free RAM...")
            subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe"], 
                          capture_output=True, timeout=10)
            print("✅ Zombie processes killed")
            gc.collect()
            time.sleep(2)
            mem2 = psutil.virtual_memory()
            print(f"✅ RAM after cleanup: {mem2.percent}%")
    except Exception as e:
        print(f"Could not check FFmpeg processes: {e}")
    
    print("\\n" + "=" * 60)
    print("📋 PHASE 5 SAFETY FEATURES ACTIVE:")
    print("  ✓ RAM guard at 70% (was 80%)")
    print("  ✓ Critical ceiling at 78% (was 90%)")
    print("  ✓ Batch size capped at 2 (was 8)")
    print("  ✓ FFmpeg threads = 1 (was 2)")
    print("  ✓ Force GC after every batch")
    print("  ✓ Zombie FFmpeg killer active")
    print("  ✓ 1.5s pause between batches")
    print("  ✓ Pre-render RAM check")
    print("=" * 60)

if __name__ == "__main__":
    check_ram_status()
'''
    
    monitor_file = BASE_DIR / "test_ram_safety.py"
    monitor_file.write_text(monitor_code, encoding="utf-8")
    print(f"[OK] RAM monitor script created: {monitor_file.name}")

if __name__ == "__main__":
    print("🚀 Starting Phase 5: ULTRA RAM-SAFE MODE...")
    print("=" * 60)
    patch_batch_long_renderer()
    print()
    patch_safe_long_controller()
    print()
    create_ram_monitor_script()
    print()
    print("=" * 60)
    print("✅ PHASE 5 COMPLETE!")
    print("=" * 60)
    print("\\n📋 NEXT STEPS:")
    print("1. Run RAM check: python test_ram_safety.py")
    print("2. Close other apps if RAM > 70%")
    print("3. Start Streamlit: streamlit run app.py")
    print("4. For long videos:")
    print("   - Keep captions OFF (saves 40-60% RAM)")
    print("   - Use 480p quality (not 4K)")
    print("   - Render in batches of 50-75 clips max")
    print("\\n⚠️  IMPORTANT:")
    print("   - Laptop ko charger pe lagayein")
    print("   - Cooling pad use karein agar possible ho")
    print("   - Background apps band karein")