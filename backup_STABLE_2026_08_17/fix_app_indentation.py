# fix_app_indentation.py
import ast
from pathlib import Path

APP_FILE = Path("app.py")

if not APP_FILE.exists():
    print("[ERROR] app.py not found!")
    exit(1)

print("🔍 Scanning app.py for indentation errors...")

with open(APP_FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed = False
max_attempts = 10

for attempt in range(max_attempts):
    try:
        # Try to parse the file. If it works, we are done!
        ast.parse("".join(lines))
        print("✅ No syntax or indentation errors found!")
        break
    except IndentationError as e:
        line_no = e.lineno
        print(f"🔧 Attempt {attempt + 1}: Fixing IndentationError at line {line_no} ({e.msg})")
        
        current_line = lines[line_no - 1]
        stripped = current_line.lstrip()
        newline_char = '\n' if current_line.endswith('\n') else ''
        
        # Find the previous non-empty line to guess the correct indentation
        prev_indent = 0
        prev_ends_with_colon = False
        for i in range(line_no - 2, -1, -1):
            prev_line = lines[i]
            if prev_line.strip():
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                if prev_line.rstrip().endswith(':'):
                    prev_ends_with_colon = True
                break
        
        # If previous line ended with ':', this line should be indented 4 more spaces
        # Otherwise, it should match the previous line's indentation
        if prev_ends_with_colon:
            target_indent = prev_indent + 4
        else:
            target_indent = prev_indent
            
        lines[line_no - 1] = ' ' * target_indent + stripped + newline_char
        print(f"   -> Adjusted line {line_no} indent to {target_indent} spaces.")
        fixed = True
        
    except SyntaxError as e:
        print(f"❌ SyntaxError at line {getattr(e, 'lineno', '?')}: {e.msg}")
        print("   This might be a real code error, not just indentation.")
        break

if fixed:
    with open(APP_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("\n✅ Indentation fixed and saved successfully!")
    print("💡 Next Step: Run 'streamlit run app.py'")
else:
    print("\n✅ File is already clean and ready to run.")