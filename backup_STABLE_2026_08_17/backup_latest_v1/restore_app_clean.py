# restore_app_clean.py
# Safely restores app.py from a working backup (No CSS injection!)
import shutil
import py_compile
from pathlib import Path

BASE_DIR = Path(r"D:\My Creation Video Generator\backup")
APP_FILE = BASE_DIR / "app.py"

print("🔍 Searching for a clean, working backup of app.py...")
print("=" * 60)

# List of possible backup names
backup_names = [
    "app.py.no_preview_backup",
    "app.py.backend_fix_backup",
    "app.py.final_3_fixes_bak",
    "app.py.backup_final_all",
    "app.py.bak_master",
    "app.py.bak_outro_wm"
]

restored = False
for name in backup_names:
    backup_path = BASE_DIR / name
    if backup_path.exists():
        print(f"Checking: {name} ... ", end="")
        try:
            # Try to compile the backup to ensure it has no syntax errors
            py_compile.compile(str(backup_path), doraise=True)
            print("✅ VALID!")
            
            # Restore it
            shutil.copy2(backup_path, APP_FILE)
            print(f"[OK] Successfully restored app.py from {name}")
            restored = True
            break
        except py_compile.PyCompileError:
            print("❌ CORRUPTED (Syntax Error)")

if not restored:
    print("\n[ERROR] No clean backup found!")
    print("Please manually check your folder for a working app.py file.")
    exit(1)

print("=" * 60)
print("✅ APP.PY RESTORED SUCCESSFULLY!")
print("=" * 60)
print("💡 Ab aap 'streamlit run app.py' chala sakte hain.")
print("💡 App bina kisi syntax error ke open ho jayega.")