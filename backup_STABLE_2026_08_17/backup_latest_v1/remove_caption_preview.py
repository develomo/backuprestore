# remove_caption_preview.py
# Completely removes Caption Preview from UI and Backend
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
APP_PY = BASE_DIR / "app.py"

if not APP_PY.exists():
    print("[ERROR] app.py not found!")
    exit(1)

# Step 1: Backup
backup = APP_PY.with_suffix(".py.no_preview_backup")
if not backup.exists():
    shutil.copy2(APP_PY, backup)
    print(f"[OK] Backup created: {backup.name}")

content = APP_PY.read_text(encoding="utf-8")
original_content = content
changes_made = 0

# Step 2: Remove Backend Functions related to "preview"
# Finds any function definition containing 'preview' and removes it entirely
pattern_func = re.compile(
    r'^([ \t]*)def\s+.*?preview.*?\(.*?\):.*?\n'
    r'((?:[ \t]+.*\n|\n)*?)'
    r'(?=^[ \t]*def |^[ \t]*class |\Z)',
    re.MULTILINE | re.IGNORECASE
)

content, n_funcs = pattern_func.subn('', content)
if n_funcs > 0:
    print(f"[OK] Removed {n_funcs} backend preview function(s).")
    changes_made += n_funcs
else:
    print("[INFO] No backend preview functions found to remove.")

# Step 3: Remove UI Section for "Caption Preview"
# Finds UI blocks starting with "Caption Preview" or "Preview Captions" and removes them
lines = content.split('\n')
new_lines = []
skip_block = False
base_indent = 0

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Check if this line starts the Caption Preview UI section
    if not skip_block and re.search(r'(?:Caption Preview|Preview Captions|Preview Section)', stripped, re.IGNORECASE):
        if stripped.startswith('st.') or stripped.startswith('#'):
            skip_block = True
            base_indent = len(line) - len(line.lstrip())
            print(f"[OK] Found UI Caption Preview block at line {i+1}, removing...")
            continue
            
    # If we are skipping lines in the preview block
    if skip_block:
        if line.strip() == '':
            continue # Skip empty lines inside the block
            
        current_indent = len(line) - len(line.lstrip())
        
        # Stop skipping if we hit a new major element at the same or lower indentation
        if current_indent <= base_indent and (stripped.startswith('st.') or stripped.startswith('def ') or stripped.startswith('class ') or stripped.startswith('if ') or stripped.startswith('for ')):
            skip_block = False
            # Don't continue, let this new line be processed
        else:
            continue # Skip this line as it's part of the preview block
            
    new_lines.append(line)
    
content = '\n'.join(new_lines)

# Step 4: Save if changes were made
if content != original_content:
    APP_PY.write_text(content, encoding="utf-8")
    print("\n✅ SUCCESS! Caption Preview section completely removed from UI and backend.")
else:
    print("\n[INFO] No Caption Preview section found to remove. It might already be gone.")

print("\n💡 Next Step: Restart your Streamlit server to see the changes.")