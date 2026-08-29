import os
import shutil
import ast

app_file = "app.py"

if not os.path.exists(app_file):
    print("❌ Error: app.py file nahi mili.")
    exit()

# Backup
shutil.copy(app_file, "app.py.before_perm_fix")

with open(app_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_main = False
main_vars_injected = False

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # 1. Catch def main() and inject robust default variables at top of main()
    if "def main():" in line or "def main(" in line:
        in_main = True
        
    if in_main and not main_vars_injected and line.strip() != "" and "def main" not in line:
        indent = " " * (len(line) - len(line.lstrip()))
        if not indent:
            indent = "    "
        
        # Inject defaults at top of main()
        vars_block = [
            f"{indent}# --- GUARANTEED CAPTION DEFAULTS ---\n",
            f"{indent}add_captions = True\n",
            f"{indent}caption_mode = 'phrase'\n",
            f"{indent}style_id = 'clean_subtitle'\n",
            f"{indent}caption_config = {{'enabled': True, 'mode': 'phrase', 'style_id': 'clean_subtitle'}}\n\n"
        ]
        # Insert right after function definition line
        new_lines.extend(vars_block)
        main_vars_injected = True

    # 2. Update variables whenever UI section returns config
    if "caption_config = render_caption_ui_section()" in line:
        indent = " " * (len(line) - len(line.lstrip()))
        update_block = [
            f"{indent}if caption_config:\n",
            f"{indent}    add_captions = caption_config.get('enabled', True)\n",
            f"{indent}    caption_mode = caption_config.get('mode', 'phrase')\n",
            f"{indent}    style_id = caption_config.get('style_id', 'clean_subtitle')\n"
        ]
        new_lines.extend(update_block)

code_str = "".join(new_lines)

# Pre-validate syntax
try:
    ast.parse(code_str)
    with open(app_file, "w", encoding="utf-8") as f:
        f.write(code_str)
    print("🚀 SUCCESS: Permanent fix applied! 'add_captions' is now safely initialized in main().")
except Exception as e:
    print(f"❌ Syntax Error during auto-fix: {e}")