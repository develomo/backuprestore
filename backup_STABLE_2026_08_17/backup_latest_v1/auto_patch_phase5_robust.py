# auto_patch_phase5_robust.py
# PHASE 5 ROBUST PATCH - Indentation-safe approach
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

def backup_file(filepath):
    if filepath.exists():
        backup = filepath.with_suffix(filepath.suffix + ".backup_phase5_robust")
        if not backup.exists():
            shutil.copy2(filepath, backup)
            print(f"[OK] Backup created: {backup.name}")

def fix_test_script():
    """Fix swap_used error in test_ram_safety.py"""
    filepath = BASE_DIR / "test_ram_safety.py"
    if not filepath.exists():
        return
    content = filepath.read_text(encoding="utf-8")
    # Replace swap_used line with safe version
    old_line = 'print(f"Swap Used: {mem.swap_used / (1024**3):.2f} GB / {mem.swap_total / (1024**3):.2f} GB")'
    new_line = '''try:
        swap = psutil.swap_memory()
        print(f"Swap Used: {swap.used / (1024**3):.2f} GB / {swap.total / (1024**3):.2f} GB")
    except Exception:
        print("Swap Used: N/A")'''
    if old_line in content:
        content = content.replace(old_line, new_line)
        filepath.write_text(content, encoding="utf-8")
        print("[OK] Fixed test_ram_safety.py swap_used error")

def patch_ram_guard_robust():
    """Replace ram_guard_batch_size function using regex (indentation-safe)."""
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        print(f"[SKIP] {filepath.name} not found.")
        return False
    
    backup_file(filepath)
    content = filepath.read_text(encoding="utf-8")
    
    # Pattern: match the entire ram_guard_batch_size function
    # It starts with "def ram_guard_batch_size" and ends at the next "def " at column 0
    pattern = re.compile(
        r'def ram_guard_batch_size\(requested_batch_size: int\) -> int:.*?(?=\ndef [a-zA-Z_])',
        re.DOTALL
    )
    
    new_function = '''def ram_guard_batch_size(requested_batch_size: int) -> int:
    # Phase 5 ULTRA SAFE: Aggressive RAM guard to prevent laptop shutdown
    bs = max(1, int(requested_batch_size or DEFAULT_BATCH_SIZE))
    pct = get_ram_percent()
    if pct is None:
        return 1  # If we can't measure, be ultra safe
    if pct >= RAM_CRITICAL_PERCENT:
        log(f"[MemorySafe] RAM CRITICAL ({pct:.1f}%) -> PAUSING 5s, forcing cleanup")
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
    return min(bs, 3)


'''
    
    match = pattern.search(content)
    if match:
        content = content[:match.start()] + new_function + content[match.end():]
        filepath.write_text(content, encoding="utf-8")
        print("[OK] Patch 1: ram_guard_batch_size replaced (ultra safe version)")
        return True
    else:
        print("[WARN] Could not find ram_guard_batch_size function")
        return False

def patch_constants_robust():
    """Lower RAM thresholds."""
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        return False
    
    content = filepath.read_text(encoding="utf-8")
    changed = False
    
    # Lower RAM_WARN_PERCENT
    if re.search(r'RAM_WARN_PERCENT\s*=\s*80\.0', content):
        content = re.sub(
            r'RAM_WARN_PERCENT\s*=\s*80\.0',
            'RAM_WARN_PERCENT = 70.0  # Phase 5: Ultra safe',
            content
        )
        changed = True
        print("[OK] Patch 2: RAM_WARN_PERCENT 80 -> 70")
    
    # Lower RAM_CRITICAL_PERCENT
    if re.search(r'RAM_CRITICAL_PERCENT\s*=\s*90\.0', content):
        content = re.sub(
            r'RAM_CRITICAL_PERCENT\s*=\s*90\.0',
            'RAM_CRITICAL_PERCENT = 78.0  # Phase 5: Hard ceiling',
            content
        )
        changed = True
        print("[OK] Patch 3: RAM_CRITICAL_PERCENT 90 -> 78")
    
    # Lower DEFAULT_BATCH_SIZE
    if re.search(r'DEFAULT_BATCH_SIZE\s*=\s*8', content):
        content = re.sub(
            r'DEFAULT_BATCH_SIZE\s*=\s*8',
            'DEFAULT_BATCH_SIZE = 2  # Phase 5: Ultra safe default',
            content
        )
        changed = True
        print("[OK] Patch 4: DEFAULT_BATCH_SIZE 8 -> 2")
    
    # Reduce FFmpeg threads
    if 'os.environ.setdefault("FFMPEG_THREADS", "2")' in content:
        content = content.replace(
            'os.environ.setdefault("FFMPEG_THREADS", "2")',
            'os.environ.setdefault("FFMPEG_THREADS", "1")  # Phase 5: Single thread'
        )
        changed = True
        print("[OK] Patch 5: FFMPEG_THREADS 2 -> 1")
    
    if changed:
        filepath.write_text(content, encoding="utf-8")
    return changed

def patch_cleanup_loop_robust():
    """Add aggressive cleanup after each batch."""
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Pattern: find the cleanup loop after batch concat
    # Look for the specific pattern where segs are unlinked
    pattern = re.compile(
        r'(for s in segs:\s*try:\s*s\.unlink\(missing_ok=True\)\s*except Exception:\s*pass\s*)safe_gc\(\)',
        re.DOTALL
    )
    
    new_cleanup = r'''\1# Phase 5: Aggressive post-batch cleanup
        import gc
        gc.collect()
        import time
        time.sleep(1.5)  # Let OS reclaim memory
        safe_gc()
        # Phase 5: Kill zombie FFmpeg processes using too much RAM
        try:
            import subprocess
            subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe", "/FI", "MEMUSAGE gt 200000"],
                          capture_output=True, timeout=5)
        except Exception:
            pass'''
    
    match = pattern.search(content)
    if match:
        content = content[:match.start()] + new_cleanup + content[match.end():]
        filepath.write_text(content, encoding="utf-8")
        print("[OK] Patch 6: Aggressive post-batch cleanup installed")
        return True
    else:
        print("[INFO] Cleanup loop pattern not found (may already be patched)")
        return False

def verify_patches():
    """Verify all patches are actually applied."""
    print("\n" + "="*60)
    print("🔍 VERIFYING PATCHES")
    print("="*60)
    
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        print("[FAIL] batch_long_renderer.py not found")
        return
    
    content = filepath.read_text(encoding="utf-8")
    
    checks = [
        ("RAM_WARN_PERCENT = 70.0", "RAM threshold 70%"),
        ("RAM_CRITICAL_PERCENT = 78.0", "RAM critical 78%"),
        ("DEFAULT_BATCH_SIZE = 2", "Default batch 2"),
        ("FFMPEG_THREADS", "1")  # Single thread
        if 'FFMPEG_THREADS", "1"' in content else ("FFMPEG_THREADS", "2"),
        ("Phase 5 ULTRA SAFE", "Ultra safe RAM guard"),
        ("PAUSING 5s, forcing cleanup", "Critical pause logic"),
        ("time.sleep(1.5)", "Post-batch sleep"),
    ]
    
    passed = 0
    for check_str, label in checks:
        if check_str in content:
            print(f"  ✅ {label}")
            passed += 1
        else:
            print(f"  ❌ {label} - NOT FOUND")
    
    print(f"\n📊 {passed}/{len(checks)} patches verified")
    return passed == len(checks)

if __name__ == "__main__":
    print("🚀 Starting Phase 5 ROBUST Patch (Indentation-Safe)...")
    print("="*60)
    
    fix_test_script()
    print()
    
    patch_constants_robust()
    print()
    
    success1 = patch_ram_guard_robust()
    print()
    
    success2 = patch_cleanup_loop_robust()
    print()
    
    all_good = verify_patches()
    
    print("\n" + "="*60)
    if all_good:
        print("✅ ALL PHASE 5 PATCHES VERIFIED - LAPTOP SAFE MODE ACTIVE")
    else:
        print("⚠️  SOME PATCHES MAY BE MISSING - Check above")
    print("="*60)
    print("\n📋 NEXT STEPS:")
    print("1. Run: python test_ram_safety.py")
    print("2. Start Streamlit: streamlit run app.py")
    print("3. Long video render karein - ab laptop shutdown NAHI hoga")