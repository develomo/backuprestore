# clean_everything.py
# 1. Silences annoying terminal prints
# 2. Aggressively removes ANY "Preview" related UI block from app.py
import re
from pathlib import Path

BASE_DIR = Path(r"D:\My Creation Video Generator\backup")

print("🚀 Starting Ultimate Clean Process...")
print("=" * 60)

# ==========================================
# TASK 1: Silence Terminal Prints
# ==========================================
files_to_silence = ["auto_edit_intelligence.py", "scene_detection_engine.py"]
for filename in files_to_silence:
    filepath = BASE_DIR / filename
    if filepath.exists():
        content = filepath.read_text(encoding="utf-8")
        lines = content.split('\n')
        new_lines = []
        silenced_count = 0
        for line in lines:
            # Comment out any print statement that starts with ✅ or is a loading message
            if line.strip().startswith('print("✅') or line.strip().startswith("print('✅") or "loaded" in line.lower() and line.strip().startswith('print'):
                new_lines.append("# " + line)
                silenced_count += 1
            else:
                new_lines.append(line)
        
        if silenced_count > 0:
            filepath.write_text('\n'.join(new_lines), encoding="utf-8")
            print(f"[OK] Silenced {silenced_count} terminal print(s) in {filename}")
        else:
            print(f"[INFO] No prints to silence in {filename}")
    else:
        print(f"[SKIP] {filename} not found")

print("-" * 60)

# ==========================================
# TASK 2: Remove Caption Preview from UI
# ==========================================
app_file = BASE_DIR / "app.py"
if app_file.exists():
    content = app_file.read_text(encoding="utf-8")
    lines = content.split('\n')
    new_lines = []
    
    skip_block = False
    skip_indent = 0
    removed_count = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect if this line starts a UI block related to "preview"
        if not skip_block and ('preview' in stripped.lower()) and (stripped.startswith('st.') or stripped.startswith('#')):
            skip_block = True
            skip_indent = len(line) - len(line.lstrip())
            print(f"[OK] Found and removing Preview UI block starting at line {i+1}: {stripped[:50]}...")
            removed_count += 1
            continue
        
        # If we are currently skipping a block
        if skip_block:
            if not line.strip():
                continue # Skip empty lines inside the block
                
            current_indent = len(line) - len(line.lstrip())
            
            # Stop skipping if we hit a new major element at the same or lower indentation
            if current_indent <= skip_indent and (stripped.startswith('st.') or stripped.startswith('if ') or stripped.startswith('for ') or stripped.startswith('def ') or stripped.startswith('class ') or stripped.startswith('else:') or stripped.startswith('elif ')):
                skip_block = False
                # Don't 'continue' here, let this new line be added to new_lines
            else:
                continue # Keep skipping this line
                
        new_lines.append(line)
        
    if removed_count > 0:
        app_file.write_text('\n'.join(new_lines), encoding="utf-8")
        print(f"[OK] Successfully removed {removed_count} Preview UI block(s) from app.py")
    else:
        print("[INFO] No Preview UI blocks found to remove. It might already be gone.")
else:
    print("[ERROR] app.py not found!")

print("=" * 60)
print("✅ CLEAN PROCESS COMPLETE!")
print("💡 Ab Streamlit server ko band karke dobara start karein.")
print("💡 Terminal clean hoga aur Caption Preview UI se gayab hoga.")