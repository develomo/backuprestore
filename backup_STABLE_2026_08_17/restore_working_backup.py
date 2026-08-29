# restore_working_backup.py
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Possible backup folder names
backup_folders = [
    "backup_latest_v1",
    "backup_latest_v2",
    "backup_latest",
    "backup_working"
]

# Files to restore
files_to_restore = [
    "batch_long_renderer.py",
    "safe_long_video_polished.py",
    "app.py",
    "master_pipeline.py"
]

print("="*70)
print("🔍 SEARCHING FOR WORKING BACKUP FOLDER...")
print("="*70)

# Find which backup folder exists
found_backup = None
for folder in backup_folders:
    folder_path = BASE_DIR / folder
    if folder_path.exists() and folder_path.is_dir():
        print(f"✅ Found: {folder}")
        found_backup = folder_path
        break

if not found_backup:
    print("❌ No backup folder found!")
    print("Please check if you have any of these folders:")
    for f in backup_folders:
        print(f"  - {f}")
    exit(1)

print(f"\n📂 Using backup from: {found_backup}")
print("="*70)

# Create safety backup of current files
print("\n🔒 Creating safety backup of current files...")
safety_backup = BASE_DIR / "safety_backup_before_restore"
safety_backup.mkdir(exist_ok=True)

for file_name in files_to_restore:
    current_file = BASE_DIR / file_name
    if current_file.exists():
        backup_file = safety_backup / file_name
        shutil.copy2(current_file, backup_file)
        print(f"  ✅ Backed up: {file_name}")

print("\n🔄 Restoring files from backup...")
print("="*70)

# Restore files from backup
restored_count = 0
for file_name in files_to_restore:
    backup_file = found_backup / file_name
    target_file = BASE_DIR / file_name
    
    if backup_file.exists():
        shutil.copy2(backup_file, target_file)
        print(f"✅ Restored: {file_name}")
        restored_count += 1
    else:
        print(f"⚠️  Not found in backup: {file_name}")

print("="*70)
print(f"\n📊 RESTORE SUMMARY:")
print(f"  • Backup folder: {found_backup.name}")
print(f"  • Files restored: {restored_count}/{len(files_to_restore)}")
print(f"  • Safety backup: {safety_backup}")

if restored_count == len(files_to_restore):
    print("\n✅ ALL FILES RESTORED SUCCESSFULLY!")
    print("\n💡 NEXT STEPS:")
    print("  1. Restart Streamlit: streamlit run app.py")
    print("  2. Test your render")
    print("  3. Everything should work as it did before!")
else:
    print("\n⚠️  Some files were not restored. Check the warnings above.")

print("="*70)