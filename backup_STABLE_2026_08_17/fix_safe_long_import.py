# fix_safe_long_import.py
# Adds missing import for safe_long_video_polished in app.py
from pathlib import Path
import py_compile

APP_FILE = Path("app.py")

if not APP_FILE.exists():
    print("[ERROR] app.py not found!")
    exit(1)

# Backup
backup = APP_FILE.with_suffix(".py.safe_long_import_backup")
if not backup.exists():
    import shutil
    shutil.copy2(APP_FILE, backup)
    print(f"[OK] Backup created: {backup.name}")

content = APP_FILE.read_text(encoding="utf-8")
lines = content.split('\n')

# Find the first 'import' line (after any initial comments/docstrings)
import_insert_idx = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('import ') or stripped.startswith('from '):
        import_insert_idx = i
        break

# Check if safe_long_video_polished is already imported
already_imported = any('safe_long_video_polished' in line for line in lines)

if not already_imported:
    # Insert the import before the first import line
    lines.insert(import_insert_idx, "import safe_long_video_polished")
    APP_FILE.write_text('\n'.join(lines), encoding="utf-8")
    print("[OK] Added 'import safe_long_video_polished' to app.py")
else:
    print("[INFO] safe_long_video_polished already imported")

# Verify syntax
try:
    py_compile.compile(str(APP_FILE), doraise=True)
    print("[OK] ✅ Syntax verification PASSED!")
    print("\n💡 NEXT STEP: Run 'streamlit run app.py' and test LONG video render")
except py_compile.PyCompileError as e:
    print(f"[ERROR] Syntax error: {e}")
    print("[INFO] Restoring from backup...")
    import shutil
    shutil.copy2(backup, APP_FILE)
    print("[OK] Restored from backup")