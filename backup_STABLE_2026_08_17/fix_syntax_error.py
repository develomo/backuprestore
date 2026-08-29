# fix_syntax_error.py
from pathlib import Path
import py_compile

TARGET = Path("batch_long_renderer.py")

if not TARGET.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = TARGET.read_text(encoding="utf-8")
lines = content.split('\n')

# Find and fix the broken line 126
fixed = False
for i, line in enumerate(lines):
    if 'fp=str(p.resolve()).replace' in line and 'unexpected character' not in line:
        # This is the broken line - replace it with correct version
        indent = len(line) - len(line.lstrip())
        lines[i] = ' ' * indent + 'fp=str(p.resolve()).replace("\\\\", "/").replace("\'", "\'\\\\\'\'")'
        print(f"[OK] Fixed line {i+1}: {line.strip()[:50]}...")
        fixed = True
        break

if fixed:
    TARGET.write_text('\n'.join(lines), encoding="utf-8")
    print("[OK] File saved. Verifying syntax...")
    
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("✅ SYNTAX VERIFICATION PASSED! File is now 100% valid.")
        print("\n💡 NEXT STEP: Run 'streamlit run app.py' and test your render!")
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error still exists: {e}")
else:
    print("[INFO] Broken line not found. File might already be fixed.")