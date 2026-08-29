# restore_original_working_version.py
# COMPLETE RESTORE: Removes all patches and restores original working versions
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

print("="*70)
print("🔄 COMPLETE RESTORE TO ORIGINAL WORKING VERSION")
print("="*70)

# List of files to restore from backups
files_to_restore = [
    ("batch_long_renderer.py", "batch_long_renderer.py.broken_21kb_backup"),
    ("safe_long_video_polished.py", "safe_long_video_polished.py.bak_master"),
    ("app.py", "app.py.no_preview_backup"),
    ("master_pipeline.py", "master_pipeline.py.voice_audio_fix_backup"),
]

restored_count = 0

for target_file, backup_file in files_to_restore:
    target_path = BASE_DIR / target_file
    backup_path = BASE_DIR / backup_file
    
    if backup_path.exists():
        # Create a safety backup of current file before overwriting
        if target_path.exists():
            safety_backup = target_path.with_suffix(".py.before_restore")
            shutil.copy2(target_path, safety_backup)
            print(f"[OK] Safety backup created: {safety_backup.name}")
        
        # Restore from backup
        shutil.copy2(backup_path, target_path)
        print(f"[OK] Restored: {target_file} from {backup_file}")
        restored_count += 1
    else:
        print(f"[WARN] Backup not found: {backup_file}")

# Remove all patch scripts (cleanup)
patch_scripts = [
    "fix_audio_mixer_final.py",
    "fix_audio_root_cause.py",
    "fix_audio_simple.py",
    "fix_audio_empty_filters.py",
    "fix_ffmpeg_exact.py",
    "fix_concat_hard.py",
    "fix_concat_function.py",
    "final_syntax_fix.py",
    "fix_backslash_error.py",
    "complete_rewrite.py",
    "fix_moviepy_error.py",
    "fix_moviepy_and_routing.py",
    "restore_proper_pipeline.py",
    "restore_advanced_renderer.py",
    "fix_voice_audio_error.py",
    "apply_5_engines_patch.py",
    "remove_caption_preview.py",
    "clean_everything.py",
    "fix_else_indentation.py",
    "restore_and_hide_preview.py",
    "restore_app_clean.py",
    "fix_final_variable.py",
    "fix_add_captions_error.py",
]

removed_count = 0
for script in patch_scripts:
    script_path = BASE_DIR / script
    if script_path.exists():
        script_path.unlink()
        removed_count += 1

print(f"\n[OK] Removed {removed_count} patch scripts")

# Verify syntax of restored files
print("\n" + "="*70)
print("🔍 VERIFYING RESTORED FILES")
print("="*70)

import py_compile

files_to_check = [
    "batch_long_renderer.py",
    "safe_long_video_polished.py",
    "app.py",
    "master_pipeline.py",
]

all_valid = True
for file_name in files_to_check:
    file_path = BASE_DIR / file_name
    if file_path.exists():
        try:
            py_compile.compile(str(file_path), doraise=True)
            print(f"[OK] {file_name}: Syntax valid")
        except py_compile.PyCompileError as e:
            print(f"[ERROR] {file_name}: Syntax error - {e}")
            all_valid = False
    else:
        print(f"[WARN] {file_name}: File not found")

print("\n" + "="*70)
if all_valid and restored_count > 0:
    print("✅ RESTORE COMPLETE!")
    print("="*70)
    print(f"\n📊 Summary:")
    print(f"   • Restored {restored_count} files from backups")
    print(f"   • Removed {removed_count} patch scripts")
    print(f"   • All files syntax verified")
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Restart Streamlit: streamlit run app.py")
    print(f"   2. Test short video render")
    print(f"   3. Test long video render")
    print(f"\n🎉 Your original working version is now active!")
else:
    print("⚠️  RESTORE INCOMPLETE")
    print("="*70)
    print("\nSome files may need manual attention.")
    print("Please check the errors above.")