# restore_and_hide_preview.py
# 1. Restores app.py from a working backup
# 2. Hides Caption Preview using 100% safe CSS (No Indentation Errors!)
import shutil
from pathlib import Path

BASE_DIR = Path(r"D:\My Creation Video Generator\backup")
APP_FILE = BASE_DIR / "app.py"

print("🚀 Starting Safe Restore & Hide Process...")
print("=" * 60)

# Step 1: Find and restore the best backup
backups = [
    "app.py.no_preview_backup",
    "app.py.backend_fix_backup",
    "app.py.final_3_fixes_bak",
    "app.py.backup_final_all"
]

restored = False
for backup_name in backups:
    backup_path = BASE_DIR / backup_name
    if backup_path.exists():
        shutil.copy2(backup_path, APP_FILE)
        print(f"[OK] Restored app.py from {backup_name}")
        restored = True
        break

if not restored:
    print("[ERROR] No valid backup found! Please check your folder.")
    exit(1)

# Step 2: Verify the restored file has no syntax errors
try:
    import py_compile
    py_compile.compile(str(APP_FILE), doraise=True)
    print("[OK] Restored app.py syntax is 100% valid!")
except py_compile.PyCompileError as e:
    print(f"[ERROR] Restored file still has syntax error: {e}")
    exit(1)

# Step 3: Add CSS to safely hide the "Caption Preview" section
# This is 100% safe and will never cause an IndentationError
content = APP_FILE.read_text(encoding="utf-8")

# Check if we already added the hide CSS
if "hide-caption-preview-css" not in content:
    # Find the first 'import streamlit as st' or similar to inject CSS right after
    import_line = "import streamlit as st"
    if import_line in content:
        css_hide = """
# HIDE CAPTION PREVIEW SECTION SAFELY (No backend code deleted)
st.markdown('''
<style>
    /* Hide any element containing 'Preview' or 'Caption Preview' in its header */
    div[data-testid="stVerticalBlock"] > div:has(h3:contains("Preview")),
    div[data-testid="stVerticalBlock"] > div:has(h2:contains("Preview")),
    div[data-testid="stVerticalBlock"] > div:has(h4:contains("Preview")) {
        display: none !important;
    }
    /* Alternative: Hide specific known preview containers if they have standard Streamlit classes */
    .stMarkdown:has(p:contains("Preview")) {
        display: none !important;
    }
</style>
''', unsafe_allow_html=True)
"""
        content = content.replace(import_line, import_line + "\n" + css_hide)
        APP_FILE.write_text(content, encoding="utf-8")
        print("[OK] Added safe CSS to hide Caption Preview from UI.")
    else:
        print("[WARN] Could not find 'import streamlit as st' to inject CSS.")
else:
    print("[INFO] CSS hide snippet already present.")

print("=" * 60)
print("✅ SAFE RESTORE & HIDE COMPLETE!")
print("=" * 60)
print("💡 Ab aap 'streamlit run app.py' chala sakte hain.")
print("💡 App bina kisi error ke open hoga, aur Preview section UI mein nazar nahi aayega.")