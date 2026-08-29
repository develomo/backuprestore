# fix_time_error.py
# Fixes UnboundLocalError: cannot access local variable 'time'
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent

def fix_batch_renderer():
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        print(f"[ERROR] {filepath.name} not found")
        return False
    
    content = filepath.read_text(encoding="utf-8")
    original_content = content
    
    # Count how many redundant imports we find
    redundant_time_imports = 0
    redundant_gc_imports = 0
    
    # Pattern 1: Remove "import time" inside functions (not at top level)
    # Top-level imports are at the start of file before any "def "
    # We need to remove "import time" that appears AFTER "def " statements
    
    lines = content.split('\n')
    new_lines = []
    in_function = False
    
    for i, line in enumerate(lines):
        # Detect if we're inside a function
        if line.strip().startswith('def '):
            in_function = True
        
        # If inside a function and line is just "import time" or "import gc"
        if in_function:
            stripped = line.strip()
            if stripped == 'import time':
                redundant_time_imports += 1
                # Skip this line (don't add to new_lines)
                continue
            elif stripped == 'import gc':
                redundant_gc_imports += 1
                # Skip this line
                continue
            elif stripped.startswith('import ') and not stripped.startswith('import subprocess'):
                # Keep other imports (like subprocess) but remove time/gc
                pass
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    if content != original_content:
        filepath.write_text(content, encoding="utf-8")
        print(f"[OK] Fixed {filepath.name}")
        print(f"     Removed {redundant_time_imports} redundant 'import time' statements")
        print(f"     Removed {redundant_gc_imports} redundant 'import gc' statements")
        return True
    else:
        print("[INFO] No redundant imports found - file may already be fixed")
        return False

def verify_fix():
    """Verify that time.time() works correctly now."""
    filepath = BASE_DIR / "batch_long_renderer.py"
    if not filepath.exists():
        return False
    
    content = filepath.read_text(encoding="utf-8")
    
    # Check that time module is imported at top level
    top_section = content[:5000]  # First 5000 chars should have top-level imports
    if 'import time' not in top_section:
        print("[WARN] 'import time' not found at top level - this is a problem")
        return False
    
    # Check that there are no "import time" inside functions
    lines = content.split('\n')
    in_function = False
    problematic_imports = []
    
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('def '):
            in_function = True
        if in_function and line.strip() == 'import time':
            problematic_imports.append(i)
    
    if problematic_imports:
        print(f"[WARN] Found 'import time' inside functions at lines: {problematic_imports}")
        return False
    
    print("[OK] Verification passed - no redundant imports inside functions")
    return True

if __name__ == "__main__":
    print("🔧 Fixing UnboundLocalError: 'time' variable...")
    print("=" * 60)
    
    if fix_batch_renderer():
        print()
        if verify_fix():
            print("\n" + "=" * 60)
            print("✅ FIX COMPLETE - Error should be resolved!")
            print("=" * 60)
            print("\n📋 Next Steps:")
            print("1. Run: streamlit run app.py")
            print("2. Test long video render")
            print("3. Laptop should NOT shutdown now")
        else:
            print("\n⚠️  Verification failed - check above")
    else:
        print("\n[INFO] File may already be fixed or no changes needed")