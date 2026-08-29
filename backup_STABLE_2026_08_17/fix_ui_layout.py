import os
import re
import shutil

POSSIBLE_FILES = ["app.py", "main.py", "gui.py", "ui.py", "dashboard.py"]

def fix_layout():
    target_file = None
    for f in POSSIBLE_FILES:
        if os.path.exists(f):
            target_file = f
            break

    if not target_file:
        print("❌ Error: Main UI file nahi mili.")
        return

    # Backup create karein
    shutil.copy(target_file, f"{target_file}.layout_bak")
    print(f"✅ Backup created: {target_file}.layout_bak")

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Purane bottom auto-patched code ko clean karein
    bottom_patch = "\n# --- AUTO-PATCHED CAPTION SECTION ---\ncaption_config = render_caption_ui_section()\n"
    content = content.replace(bottom_patch, "")
    content = content.replace("caption_config = render_caption_ui_section()", "")

    # Ensure Import line top par maujood ho
    if "from ui_caption_section import render_caption_ui_section" not in content:
        content = "from ui_caption_section import render_caption_ui_section\n" + content

    # 2. Match pattern for old 'Caption & Subtitle Settings Optional' section
    # Regex to capture old caption section block
    old_caption_pattern = r"(#?\s*.*Caption & Subtitle Settings[\s\S]*?)(?=\n\s*(#|st\.header|st\.subheader|st\.divider|st\.markdown|\Z))"
    
    new_caption_call = "\n# --- NEW DYNAMIC CAPTION ENGINE SECTION ---\ncaption_config = render_caption_ui_section()\n"

    if re.search(old_caption_pattern, content, re.IGNORECASE):
        # Purane section ki jagah naye Dynamic Caption Engine ko substitute kar dein
        content = re.sub(old_caption_pattern, new_caption_call, content, count=1, flags=re.IGNORECASE)
        print("✅ Purana section remove karke naya 'Dynamic Subtitle & Caption Engine' Volume Mixer ke niche place kar diya gaya hai.")
    else:
        # Fallback: Agar header text matching na ho, to Volume Mixer ke niche insert karein
        mixer_pattern = r"(Multi-Track Audio Volume Mixer[\s\S]*?)(?=\n\s*(#|st\.header|st\.subheader|st\.divider|st\.markdown|\Z))"
        if re.search(mixer_pattern, content):
            content = re.sub(mixer_pattern, r"\1" + new_caption_call, content, count=1)
            print("✅ 'Dynamic Subtitle & Caption Engine' Volume Mixer ke niche shift kar diya gaya hai.")

    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)

    print("🚀 Layout successfully updated!")

if __name__ == "__main__":
    fix_layout()