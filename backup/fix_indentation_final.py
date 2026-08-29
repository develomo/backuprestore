# fix_indentation_final.py
# FINAL FIX: Restore backup + Add properly indented has_sfx definition
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

def restore_and_fix():
    # Step 1: Restore from backup
    backup_candidates = [
        "batch_long_renderer.py.backup_final_all",
        "batch_long_renderer.py.broadcast_backup",
        "batch_long_renderer.py.broadcast_v2_backup",
        "batch_long_renderer.py.backup_4issues",
        "batch_long_renderer.py.backup_4issues_clean",
    ]
    
    target = BASE_DIR / "batch_long_renderer.py"
    restored = False
    
    for backup_name in backup_candidates:
        backup = BASE_DIR / backup_name
        if backup.exists():
            shutil.copy2(backup, target)
            print(f"[OK] Restored from {backup_name}")
            restored = True
            break
    
    if not restored:
        print("[ERROR] No backup found!")
        return False
    
    # Step 2: Read and fix the mux_audio_timeline function
    content = target.read_text(encoding="utf-8")
    lines = content.split('\n')
    
    # Find the mux_audio_timeline function
    mux_start = None
    for i, line in enumerate(lines):
        if 'def mux_audio_timeline(' in line:
            mux_start = i
            break
    
    if mux_start is None:
        print("[ERROR] mux_audio_timeline function not found!")
        return False
    
    # Find the line with "has_music = bool(music and Path(music).exists())"
    has_music_line = None
    for i in range(mux_start, min(mux_start + 50, len(lines))):
        if 'has_music = bool(music and Path(music).exists())' in lines[i]:
            has_music_line = i
            break
    
    if has_music_line is None:
        print("[ERROR] has_music definition not found!")
        return False
    
    # Check if has_sfx is already defined right after has_music
    has_sfx_defined = False
    for i in range(has_music_line + 1, min(has_music_line + 5, len(lines))):
        if 'has_sfx = bool(sfx and Path(sfx).exists())' in lines[i]:
            has_sfx_defined = True
            print("[INFO] has_sfx already properly defined")
            break
    
    if not has_sfx_defined:
        # Get the indentation of has_music line
        has_music_indent = len(lines[has_music_line]) - len(lines[has_music_line].lstrip())
        indent_str = ' ' * has_music_indent
        
        # Insert has_sfx definition right after has_music
        new_line = f"{indent_str}has_sfx = bool(sfx and Path(sfx).exists())"
        lines.insert(has_music_line + 1, new_line)
        print(f"[OK] Added has_sfx definition at line {has_music_line + 2}")
    
    # Write back
    target.write_text('\n'.join(lines), encoding="utf-8")
    print("[OK] File saved successfully")
    
    # Step 3: Verify no syntax errors
    try:
        compile(target.read_text(encoding="utf-8"), str(target), 'exec')
        print("[OK] No syntax errors detected!")
        return True
    except SyntaxError as e:
        print(f"[ERROR] Syntax error still present: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Starting FINAL INDENTATION FIX...")
    print("=" * 60)
    
    if restore_and_fix():
        print("\n" + "=" * 60)
        print("✅ FIX COMPLETE!")
        print("=" * 60)
        print("\n📋 NEXT STEPS:")
        print("1. Run: streamlit run app.py")
        print("2. Test Long Video render")
        print("3. No more indentation errors!")
    else:
        print("\n❌ Fix failed - check errors above")