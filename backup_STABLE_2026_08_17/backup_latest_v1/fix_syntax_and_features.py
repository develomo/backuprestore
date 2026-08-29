# fix_syntax_and_features.py
# Fixes syntax error at line 1188 + applies outro/subscribe/speed fixes
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
TARGET = BASE_DIR / "batch_long_renderer.py"

def fix_line_1188_syntax():
    """Fix the broken syntax at line 1188"""
    if not TARGET.exists():
        print(f"[ERROR] {TARGET.name} not found")
        return False
    
    content = TARGET.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # Find and fix line 1188 (or nearby lines with the broken pattern)
    fixed = False
    for i, line in enumerate(lines):
        # Look for the broken pattern: semicolon-separated statements with if/raise
        if 'outro_out=batch_dir' in line and '; if not outputs:' in line:
            # This is the broken line - split it into proper multi-line
            indent = '        '  # 8 spaces
            
            # Replace with properly formatted multi-line code
            new_lines = [
                f'{indent}outro_out = batch_dir / f"batch_{{len(outputs)+1:04d}}_outro.mp4"',
                f'{indent}normalize_video_asset(outro, outro_out, size, fps, outro_sec, quality)',
                f'{indent}outputs.append(outro_out)',
                f'{indent}if not outputs:',
                f'{indent}    raise RuntimeError("No visual outputs rendered")',
            ]
            
            # Replace the broken line with new_lines
            lines[i:i+1] = new_lines
            fixed = True
            print(f"[OK] Fixed syntax error at line {i+1}")
            break
    
    if not fixed:
        print("[INFO] Line 1188 syntax error not found - may already be fixed")
    
    TARGET.write_text('\n'.join(lines), encoding="utf-8")
    return True

def apply_feature_fixes():
    """Apply outro, subscribe, and speed fixes"""
    content = TARGET.read_text(encoding="utf-8")
    original = content
    changes = 0
    
    # FIX 1: Speed boost - threads 2 to 0
    if '"-threads", "2"' in content:
        content = content.replace('"-threads", "2"', '"-threads", "0"')
        print("[OK] Fix 1: FFmpeg speed boosted (threads=0)")
        changes += 1
    
    # FIX 2: Subscribe overlay position - top-right to bottom-right
    if 'corner="top-right"' in content:
        content = content.replace('corner="top-right"', 'corner="bottom-right"')
        print("[OK] Fix 2: Subscribe overlay moved to bottom-right")
        changes += 1
    
    # FIX 3: Subscribe overlay timeout - 180s to 600s
    if 'timeout=180)' in content:
        content = content.replace('timeout=180)', 'timeout=600)')
        print("[OK] Fix 3: Subscribe overlay timeout increased to 600s")
        changes += 1
    
    # FIX 4: Outro - ensure it's appended AFTER looping (not before)
    # Look for the pattern where outro is added before video_raw is created
    old_pattern = '''outputs.append(outro_out)
        if not outputs:
            raise RuntimeError("No visual outputs rendered")
        video_raw = temp / "video_raw.mp4"
        concat_files(outputs, video_raw'''
    
    new_pattern = '''# FIX: Separate main body from outro
        main_outputs = [p for p in outputs if "outro" not in str(p)]
        video_raw = temp / "video_raw.mp4"
        if not main_outputs:
            raise RuntimeError("No visual outputs rendered")
        concat_files(main_outputs, video_raw'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print("[OK] Fix 4: Outro separated from main body (will be appended after looping)")
        changes += 1
    
    if changes == 0:
        print("[INFO] No additional feature fixes needed")
    
    if content != original:
        TARGET.write_text(content, encoding="utf-8")
    
    return changes > 0

def verify_syntax():
    """Final syntax verification"""
    try:
        import py_compile
        py_compile.compile(str(TARGET), doraise=True)
        print("[OK] Final syntax verification PASSED")
        return True
    except py_compile.PyCompileError as e:
        print(f"[ERROR] Syntax error still exists: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Syntax Fix + Feature Fixes")
    print("=" * 60)
    
    if not fix_line_1188_syntax():
        print("[FAIL] Could not fix line 1188 syntax")
        exit(1)
    
    print()
    
    if not apply_feature_fixes():
        print("[INFO] No feature fixes applied")
    
    print()
    
    if not verify_syntax():
        print("[FAIL] Syntax verification failed")
        exit(1)
    
    print("=" * 60)
    print("✅ ALL FIXES APPLIED SUCCESSFULLY!")
    print("=" * 60)
    print("\nNext: streamlit run app.py")