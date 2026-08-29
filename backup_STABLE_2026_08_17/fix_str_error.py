# fix_str_error.py - ABSOLUTE FINAL VERSION
from pathlib import Path

app = Path("app.py")
lines = app.read_text(encoding="utf-8").split('\n')

fixed = False

for i in range(len(lines)):
    stripped = lines[i].strip()
    
    # Fix: wm_opacity=0.6 without trailing comma
    if stripped == 'wm_opacity=0.6':
        indent = len(lines[i]) - len(lines[i].lstrip())
        lines[i] = ' ' * indent + 'wm_opacity=0.6,'
        fixed = True
        print(f"✅ FIXED line {i+1}: Added missing comma after wm_opacity=0.6")
        break
    
    # Also handle if extra ) is still there
    if stripped == 'wm_opacity=0.6),':
        indent = len(lines[i]) - len(lines[i].lstrip())
        lines[i] = ' ' * indent + 'wm_opacity=0.6,'
        fixed = True
        print(f"✅ FIXED line {i+1}: Removed extra ) and added comma")
        break

if not fixed:
    print("⚠️ Pattern not found. Showing all wm_opacity lines:")
    for i, line in enumerate(lines):
        if 'wm_opacity' in line:
            print(f"   Line {i+1}: '{line.strip()}'")
else:
    app.write_text('\n'.join(lines), encoding="utf-8")

# Verify
try:
    compile(app.read_text(encoding="utf-8"), "app.py", "exec")
    print("✅ Syntax verification PASSED!")
    print("💡 NEXT: Run 'streamlit run app.py'")
except SyntaxError as e:
    print(f"❌ Error at line {e.lineno}: {e.msg}")
    err_lines = app.read_text(encoding="utf-8").split('\n')
    for j in range(max(0, e.lineno-3), min(len(err_lines), e.lineno+2)):
        marker = ">>>" if j == e.lineno - 1 else "   "
        print(f"{marker} {j+1}: {err_lines[j]}")