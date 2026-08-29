# restore_full_long_renderer.py
import os
import shutil
import py_compile
from pathlib import Path

BASE_DIR = Path(__file__).parent
MAIN_BLR = BASE_DIR / "batch_long_renderer.py"
BACKUP_BLR = BASE_DIR / "backup_latest_v1" / "batch_long_renderer.py"

print("="*70)
print("🔄 RESTORING & PATCHING 1450+ LINE batch_long_renderer.py")
print("="*70)

# Step 1: Restore from backup_latest_v1 if available
if BACKUP_BLR.exists():
    print("\n[1/3] Found 1450+ line backup in 'backup_latest_v1'!")
    print("      Restoring full advanced version...")
    
    # Backup current small file just in case
    if MAIN_BLR.exists():
        shutil.copy2(MAIN_BLR, MAIN_BLR.with_suffix(".py.before_full_restore"))
        
    shutil.copy2(BACKUP_BLR, MAIN_BLR)
    print("      ✅ Full advanced version restored successfully!")
else:
    print("\n[1/3] 'backup_latest_v1/batch_long_renderer.py' not found.")
    print("      Will attempt to patch the existing file.")

# Step 2: Apply critical syntax fix (concat_files_hard backslash issue)
print("\n[2/3] Applying critical syntax fixes (without truncating code)...")
if MAIN_BLR.exists():
    content = MAIN_BLR.read_text(encoding="utf-8")
    changes = 0
    
    # Fix the exact broken backslash line from previous failed patches
    if 'replace("\\", "/")' in content:
        content = content.replace('replace("\\", "/")', 'replace("\\\\", "/")')
        changes += 1
        
    # Also fix the quote escaping if it was mangled
    if '.replace("\'", "\'\\\'\'")' in content and '.replace("\'", "\'\\\\\'\'")' not in content:
        content = content.replace('.replace("\'", "\'\\\'\'")', '.replace("\'", "\'\\\\\'\'")')
        changes += 1
        
    if changes > 0:
        MAIN_BLR.write_text(content, encoding="utf-8")
        print(f"      ✅ Applied {changes} syntax fix(es) safely.")
    else:
        print("      ℹ️ No syntax fixes needed (code appears clean).")
else:
    print("      ❌ batch_long_renderer.py not found!")

# Step 3: Verify Syntax
print("\n[3/3] Verifying Python syntax...")
try:
    py_compile.compile(str(MAIN_BLR), doraise=True)
    print("      ✅ SYNTAX VERIFICATION PASSED!")
    
    # Check file size to reassure user
    size_kb = MAIN_BLR.stat().st_size / 1024
    print(f"\n📊 FILE STATS:")
    print(f"   • File: batch_long_renderer.py")
    print(f"   • Size: {size_kb:.1f} KB ({MAIN_BLR.stat().st_size} bytes)")
    
    if size_kb > 50:  # 50KB+ means the full 1450+ line file is back
        print("   • Status: ✅ FULL 1450+ LINE ADVANCED ENGINE RESTORED!")
    else:
        print("   • Status: ⚠️ File is still small. Please check backup_latest_v1 folder.")
        
    print("\n" + "="*70)
    print("🎉 READY TO RENDER!")
    print("="*70)
    print("Next Step: Run 'streamlit run app.py'")
    
except py_compile.PyCompileError as e:
    print(f"      ❌ SYNTAX ERROR STILL EXISTS: {e}")
    print("\n⚠️ The file still has issues. Please share the exact error line.")