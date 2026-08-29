# fix_else_indentation.py
# Fixes IndentationError caused by empty 'else:' blocks
from pathlib import Path

BASE_DIR = Path(r"D:\My Creation Video Generator\backup")
APP_FILE = BASE_DIR / "app.py"

if not APP_FILE.exists():
    print("[ERROR] app.py not found!")
    exit(1)

print("🔍 Scanning app.py for empty 'else:' blocks...")

content = APP_FILE.read_text(encoding="utf-8")
lines = content.split('\n')
new_lines = []
fixed_count = 0

for i, line in enumerate(lines):
    new_lines.append(line)
    
    stripped = line.strip()
    # Check if this line is an 'else:' or 'elif ...:'
    if stripped.startswith('else:') or stripped.startswith('elif '):
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            next_stripped = next_line.strip()
            
            current_indent = len(line) - len(line.lstrip())
            next_indent = len(next_line) - len(next_line.lstrip())
            
            # If the next line is not empty, but has same or less indentation, 
            # it means the 'else' block is empty and will cause an IndentationError.
            if next_stripped != '' and next_indent <= current_indent:
                # Add 'pass' with correct indentation (current + 4 spaces)
                pass_line = ' ' * (current_indent + 4) + 'pass'
                new_lines.append(pass_line)
                fixed_count += 1
                print(f"[OK] Added 'pass' to empty block after line {i+1}: {stripped}")

if fixed_count > 0:
    APP_FILE.write_text('\n'.join(new_lines), encoding="utf-8")
    print(f"\n✅ SUCCESS! Fixed {fixed_count} indentation error(s).")
    print("💡 Ab aap 'streamlit run app.py' dobara chala sakte hain.")
else:
    print("\n[INFO] No empty 'else' blocks found. Error might be elsewhere.")