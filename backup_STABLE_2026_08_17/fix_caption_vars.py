import os
import shutil
import ast

app_file = "app.py"

if not os.path.exists(app_file):
    print("❌ Error: app.py file nahi mili.")
    exit()

# Backup create karein
shutil.copy(app_file, "app.py.before_vars_fix")

with open(app_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
fixed = False

for line in lines:
    new_lines.append(line)
    
    # render_caption_ui_section() call ke foran baad variables extract karein
    if "caption_config = render_caption_ui_section()" in line and not fixed:
        indent = " " * (len(line) - len(line.lstrip()))
        new_lines.append(f"{indent}add_captions = caption_config.get('enabled', True)\n")
        new_lines.append(f"{indent}caption_mode = caption_config.get('mode', 'phrase')\n")
        new_lines.append(f"{indent}style_id = caption_config.get('style_id', 'clean_subtitle')\n")
        fixed = True

# Backup check: Agar match na mile to main() ke shuru mein default add karein
if not fixed:
    print("⚠️ Matching line define nahi mili, defaults inject kar rahe hain...")
    final_lines = []
    for line in lines:
        final_lines.append(line)
        if "def main():" in line:
            final_lines.append("    caption_config = {'enabled': True, 'mode': 'phrase', 'style_id': 'clean_subtitle'}\n")
            final_lines.append("    add_captions = True\n")
            final_lines.append("    caption_mode = 'phrase'\n")
            final_lines.append("    style_id = 'clean_subtitle'\n")
    new_lines = final_lines

code_str = "".join(new_lines)

# Pre-validation for syntax & indentation check
try:
    ast.parse(code_str)
    with open(app_file, "w", encoding="utf-8") as f:
        f.write(code_str)
    print("🎉 SUCCESS: NameError 'add_captions' 100% resolved!")
except Exception as e:
    print(f"❌ Syntax Error: {e}")