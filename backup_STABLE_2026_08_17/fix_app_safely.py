import os
import shutil

app_file = "app.py"
backup_file = "app.py.layout_bak"

# 1. Restore pristine backup first
if os.path.exists(backup_file):
    shutil.copy(backup_file, app_file)
    print("✅ App.py backup se restore ho gayi hai.")
elif os.path.exists("app.py.ui_backup"):
    shutil.copy("app.py.ui_backup", app_file)
    print("✅ App.py original backup se restore ho gayi hai.")

with open(app_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
i = 0
in_old_caption_block = False

while i < len(lines):
    line = lines[i]
    
    # Purane 'Caption & Subtitle Settings' header ya controls ki line detect karein
    if "Caption & Subtitle Settings" in line or "Enable Dynamic Animated Captions" in line:
        in_old_caption_block = True
        # Parent block ka indent space measure karein
        indent = " " * (len(line) - len(line.lstrip()))
        
        # Sahi indentation ke sath naya component add karein
        new_lines.append(f"{indent}# --- DYNAMIC CAPTION ENGINE SECTION ---\n")
        new_lines.append(f"{indent}caption_config = render_caption_ui_section()\n")
        i += 1
        continue

    if in_old_caption_block:
        # Purani lines ko skip karein jab tak naya header ya block na aaye
        stripped = line.strip()
        if any(h in line for h in ["Quality Score", "Video & Audio Editing", "st.header", "st.subheader", "def "]) and not ("Caption & Subtitle" in line):
            in_old_caption_block = False
            new_lines.append(line)
        i += 1
        continue

    new_lines.append(line)
    i += 1

content = "".join(new_lines)

# Ensure top-level import exists
if "from ui_caption_section import render_caption_ui_section" not in content:
    content = "from ui_caption_section import render_caption_ui_section\n" + content

with open(app_file, "w", encoding="utf-8") as f:
    f.write(content)

print("🚀 Indentation error fix ho gaya hai aur UI layout perfectly align kar diya gaya hai!")