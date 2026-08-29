# fix_app_final.py - FINAL DEFINITIVE FIX FOR app.py
from pathlib import Path

app = Path("app.py")
lines = app.read_text(encoding="utf-8").split('\n')

changes = []

for i in range(len(lines)):
    stripped = lines[i].strip()
    
    # FIX 1: Remove extra ) from subscribe_overlay line
    if stripped == 'subscribe_overlay=assets.get("subscribe")),':
        indent = len(lines[i]) - len(lines[i].lstrip())
        lines[i] = ' ' * indent + 'subscribe_overlay=assets.get("subscribe"),'
        changes.append(f"Line {i+1}: Removed extra ')' from subscribe_overlay")
    
    # FIX 2: Remove duplicate subscribe_overlay line
    elif stripped == 'subscribe_overlay=subscribe_overlay,' or stripped == 'subscribe_overlay=subscribe_overlay)':
        lines[i] = ''  # Mark for removal
        changes.append(f"Line {i+1}: REMOVED duplicate subscribe_overlay")
    
    # FIX 3: Ensure str(output_file) is properly closed
    elif 'output_path=str(output_file,' in stripped and ')' not in stripped.split('str(output_file,')[1]:
        indent = len(lines[i]) - len(lines[i].lstrip())
        lines[i] = ' ' * indent + 'output_path=str(output_file),'
        changes.append(f"Line {i+1}: Closed str(output_file) properly")

# Remove empty lines (marked duplicates)
new_lines = [line for line in lines if line != '']

app.write_text('\n'.join(new_lines), encoding="utf-8")

if changes:
    print("✅ FIXES APPLIED:")
    for c in changes:
        print(f"   • {c}")
else:
    print("ℹ️ No fixes needed")

# Verify syntax
try:
    compile(app.read_text(encoding="utf-8"), "app.py", "exec")
    print("\n✅ Syntax verification PASSED!")
    print("💡 NEXT: Run 'streamlit run app.py'")
except SyntaxError as e:
    print(f"\n❌ Error at line {e.lineno}: {e.msg}")
    err_lines = app.read_text(encoding="utf-8").split('\n')
    for j in range(max(0, e.lineno-3), min(len(err_lines), e.lineno+2)):
        marker = ">>>" if j == e.lineno - 1 else "   "
        print(f"{marker} {j+1}: {err_lines[j]}")