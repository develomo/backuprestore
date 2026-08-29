# fix_backslash_syntax.py
import py_compile
from pathlib import Path

BLR_PATH = Path("batch_long_renderer.py")

if not BLR_PATH.exists():
    print("[ERROR] batch_long_renderer.py not found!")
    exit(1)

content = BLR_PATH.read_text(encoding="utf-8")
lines = content.split('\n')
fixed = False

for i, line in enumerate(lines):
    # Find the exact broken line (it might use 'safe_path' or 'fp')
    if 'str(c.resolve()).replace' in line and 'SyntaxError' not in line:
        indent = len(line) - len(line.lstrip())
        # Correctly escaped backslashes for Python
        lines[i] = ' ' * indent + 'safe_path = str(c.resolve()).replace("\\\\", "/").replace("\'", "\'\\\\\'\'")'
        print(f"[OK] Fixed line {i+1}: {lines[i].strip()}")
        fixed = True
        break

if fixed:
    BLR_PATH.write_text('\n'.join(lines), encoding="utf-8")
    print("[OK] File saved. Verifying syntax...")
    
    try:
        py_compile.compile(str(BLR_PATH), doraise=True)
        print("✅ SYNTAX VERIFICATION PASSED! File is now 100% valid.")
        print("\n💡 NEXT STEP: Run 'streamlit run app.py' and test your render!")
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error still exists: {e}")
else:
    print("[INFO] Broken line not found. File might already be fixed.")