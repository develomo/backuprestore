# fix_line_436.py
from pathlib import Path

file_path = Path("batch_long_renderer.py")
lines = file_path.read_text(encoding="utf-8").split('\n')

fixed = False
for i, line in enumerate(lines):
    # Find the exact broken line
    if 'transition_time = 1.5 + (i * clip_duration_avg)' in line:
        indent = len(line) - len(line.lstrip())
        # Replace with hardcoded safe values (no variable dependency)
        lines[i] = ' ' * indent + 'transition_time = 1.5 + (i * 7.0) - (i * 0.65)  # Fixed: hardcoded values'
        print(f"✅ FIXED line {i+1}: Replaced variable references with safe constants")
        fixed = True
        break

if fixed:
    file_path.write_text('\n'.join(lines), encoding="utf-8")
    
    # Verify syntax
    try:
        compile('\n'.join(lines), str(file_path), "exec")
        print("✅ Syntax verification PASSED!")
        print("💡 NEXT: Run 'streamlit run app.py'")
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
else:
    print("⚠️ Could not find the exact line to fix")
    print("   Searching for similar patterns...")
    for i, line in enumerate(lines):
        if 'clip_duration_avg' in line and 'transition_time' in line:
            print(f"   Found similar at line {i+1}: {line.strip()}")