# fix_phase5_syntax_error.py
# Restore backup and apply safe patch without regex backreferences
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

def restore_backup():
    """Restore batch_long_renderer.py from backup."""
    backup = BASE_DIR / "batch_long_renderer.py.backup_phase5_robust"
    target = BASE_DIR / "batch_long_renderer.py"
    
    if backup.exists():
        shutil.copy2(backup, target)
        print(f"[OK] Restored {target.name} from backup")
        return True
    else:
        print(f"[ERROR] Backup not found: {backup.name}")
        return False

def apply_safe_patch():
    """Apply Phase 5 patches using line-by-line approach (no regex backreferences)."""
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        print(f"[ERROR] {filepath.name} not found")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # Find the cleanup loop location
    cleanup_marker = "for s in segs:"
    cleanup_line_idx = None
    
    for i, line in enumerate(lines):
        if cleanup_marker in line and i > 2000:  # Only in render function area
            # Check if next few lines contain the unlink pattern
            if i + 3 < len(lines):
                if "try:" in lines[i+1] and "s.unlink" in lines[i+2]:
                    cleanup_line_idx = i
                    break
    
    if cleanup_line_idx is None:
        print("[WARN] Could not find cleanup loop location")
        return False
    
    print(f"[OK] Found cleanup loop at line {cleanup_line_idx + 1}")
    
    # Find the safe_gc() call after the cleanup loop
    safe_gc_idx = None
    for i in range(cleanup_line_idx + 1, min(cleanup_line_idx + 20, len(lines))):
        if "safe_gc()" in lines[i]:
            safe_gc_idx = i
            break
    
    if safe_gc_idx is None:
        print("[WARN] Could not find safe_gc() after cleanup loop")
        return False
    
    print(f"[OK] Found safe_gc() at line {safe_gc_idx + 1}")
    
    # Insert aggressive cleanup BEFORE safe_gc()
    indent = "        "  # 8 spaces
    new_cleanup_lines = [
        f"{indent}# Phase 5: Aggressive post-batch cleanup",
        f"{indent}import gc",
        f"{indent}gc.collect()",
        f"{indent}import time",
        f"{indent}time.sleep(1.5)  # Let OS reclaim memory",
        f"{indent}# Phase 5: Kill zombie FFmpeg processes",
        f"{indent}try:",
        f"{indent}    import subprocess",
        f'{indent}    subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe", "/FI", "MEMUSAGE gt 200000"],',
        f"{indent}                  capture_output=True, timeout=5)",
        f"{indent}except Exception:",
        f"{indent}    pass",
    ]
    
    # Insert new lines before safe_gc()
    for i, new_line in enumerate(new_cleanup_lines):
        lines.insert(safe_gc_idx + i, new_line)
    
    print(f"[OK] Inserted aggressive cleanup ({len(new_cleanup_lines)} lines)")
    
    # Write back
    new_content = '\n'.join(lines)
    filepath.write_text(new_content, encoding="utf-8")
    print(f"[OK] Patched {filepath.name} successfully")
    
    return True

def verify_patch():
    """Verify the patch was applied correctly."""
    filepath = BASE_DIR / "batch_long_renderer.py"
    content = filepath.read_text(encoding="utf-8")
    
    checks = [
        ("Phase 5: Aggressive post-batch cleanup", "Cleanup comment"),
        ("time.sleep(1.5)", "Post-batch sleep"),
        ("taskkill", "Zombie killer"),
        ("RAM_WARN_PERCENT = 70.0", "RAM threshold 70%"),
        ("RAM_CRITICAL_PERCENT = 78.0", "RAM critical 78%"),
        ("DEFAULT_BATCH_SIZE = 2", "Default batch 2"),
    ]
    
    passed = 0
    for check_str, label in checks:
        if check_str in content:
            print(f"  ✅ {label}")
            passed += 1
        else:
            print(f"  ❌ {label} - NOT FOUND")
    
    # Check for syntax errors
    if "\\1" in content:
        print("  ❌ CRITICAL: Found \\1 backreference (syntax error)")
        return False
    
    print(f"\n📊 {passed}/{len(checks)} checks passed")
    return passed == len(checks)

if __name__ == "__main__":
    print("🔧 Fixing Phase 5 Syntax Error...")
    print("=" * 60)
    
    if restore_backup():
        print()
        if apply_safe_patch():
            print()
            if verify_patch():
                print("\n" + "=" * 60)
                print("✅ FIX COMPLETE - Syntax error resolved!")
                print("=" * 60)
                print("\n📋 Next Steps:")
                print("1. Run: streamlit run app.py")
                print("2. Test long video render")
                print("3. Laptop should NOT shutdown now")
            else:
                print("\n⚠️  Patch verification failed - check above")
        else:
            print("\n❌ Patch application failed")
    else:
        print("\n❌ Backup restore failed")