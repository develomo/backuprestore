import os
import shutil

# Common UI entry point filenames
POSSIBLE_UI_FILES = ["app.py", "main.py", "gui.py", "ui.py", "dashboard.py"]

IMPORT_LINE = "\nfrom ui_caption_section import render_caption_ui_section\n"
RENDER_CALL_LINE = "\n# --- AUTO-PATCHED CAPTION SECTION ---\ncaption_config = render_caption_ui_section()\n"

def patch_ui_file():
    target_file = None
    
    # Auto-detect existing UI file
    for f in POSSIBLE_UI_FILES:
        if os.path.exists(f):
            target_file = f
            break

    if not target_file:
        print("❌ Error: Koi standard UI file (app.py, main.py, gui.py) nahi mili.")
        print("Aap apni main UI file ka naam bataen taake usay patch kiya ja sake.")
        return

    print(f"🎯 Found UI file: '{target_file}'")

    # Safe backup
    backup_path = f"{target_file}.ui_backup"
    shutil.copy(target_file, backup_path)
    print(f"✅ Backup created: '{backup_path}'")

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    if "render_caption_ui_section" in content:
        print("⚠️ UI file pehle se patched hai.")
        return

    # Add import at top
    updated_content = IMPORT_LINE + content + "\n" + RENDER_CALL_LINE

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"🚀 Success! Caption UI section automatically injected into '{target_file}'.")

if __name__ == "__main__":
    patch_ui_file()