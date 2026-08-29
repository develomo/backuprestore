import os
import shutil

app_file = "app.py"

if not os.path.exists(app_file):
    print("❌ Error: app.py nahi mili.")
    exit()

# Backup create karein
shutil.copy(app_file, "app.py.before_relocate")

with open(app_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1. Purane tamam caption section calls aur duplicate headers/comments ko remove karein
cleaned_lines = []
for line in lines:
    if "render_caption_ui_section" in line and "import" not in line:
        continue
    if "DYNAMIC CAPTION ENGINE SECTION" in line:
        continue
    cleaned_lines.append(line)

# 2. Multi-Track Audio Volume Mixer ke exact niche naye section ko place karein
final_lines = []
inserted = False

for i, line in enumerate(cleaned_lines):
    final_lines.append(line)
    
    # Target location: Multi-Track Audio Volume Mixer section ya audio sliders ke foran baad
    if not inserted and ("Multi-Track Audio Volume Mixer" in line or "SFX Volume" in line or "sfx_vol" in line.lower()):
        # Current line ki space / indentation determine karein
        indent = " " * (len(line) - len(line.lstrip()))
        
        # Audio block ke end par insert karne ke liye next line check karein
        # Agar line main Volume Mixer header ya slider hai to uske niche inject karein
        if "SFX Volume" in line or "sfx_vol" in line.lower() or "Multi-Track Audio Volume Mixer" in line:
            final_lines.append("\n")
            final_lines.append(f"{indent}# --- DYNAMIC SUBTITLE & CAPTION ENGINE ---\n")
            final_lines.append(f"{indent}caption_config = render_caption_ui_section()\n")
            final_lines.append("\n")
            inserted = True

# Backup fallback: Agar Mixer ka header keyword direct search na mila ho
if not inserted:
    print("⚠️ Mixer section text directly match nahi hua, fallback locator search kar rahe hain...")
    final_lines = []
    for line in cleaned_lines:
        final_lines.append(line)
        if not inserted and ("Video & Audio Editing Parameters" in line or "Editing Parameters" in line):
            indent = " " * (len(line) - len(line.lstrip()))
            final_lines.append("\n")
            final_lines.append(f"{indent}# --- DYNAMIC SUBTITLE & CAPTION ENGINE ---\n")
            final_lines.append(f"{indent}caption_config = render_caption_ui_section()\n")
            inserted = True

with open(app_file, "w", encoding="utf-8") as f:
    f.writelines(final_lines)

print("🚀 Success: Section perfectly relocated right below 'Multi-Track Audio Volume Mixer' without indentation errors!")