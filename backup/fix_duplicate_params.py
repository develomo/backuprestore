# fix_duplicate_params.py - REMOVES DUPLICATE KEYWORD ARGUMENTS
from pathlib import Path

app = Path("app.py")
lines = app.read_text(encoding="utf-8").split('\n')

# Track which params we've already seen in the current function call
seen_params = set()
lines_to_remove = []
in_pipeline_call = False

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Detect start of run_integrated_long_pipeline call
    if 'run_integrated_long_pipeline(' in line:
        in_pipeline_call = True
        seen_params = set()
        continue
    
    # Detect end of function call
    if in_pipeline_call and stripped.endswith(')'):
        in_pipeline_call = False
        continue
    
    # Inside the call, check for duplicate keyword arguments
    if in_pipeline_call and '=' in stripped and not stripped.startswith('#'):
        param_name = stripped.split('=')[0].strip().rstrip(',')
        
        if param_name in seen_params:
            lines_to_remove.append(i)
            print(f"🗑️  REMOVING duplicate line {i+1}: {stripped[:60]}")
        else:
            seen_params.add(param_name)

if lines_to_remove:
    # Remove duplicate lines (reverse order to preserve indices)
    for idx in sorted(lines_to_remove, reverse=True):
        del lines[idx]
    
    app.write_text('\n'.join(lines), encoding="utf-8")
    print(f"\n✅ Removed {len(lines_to_remove)} duplicate parameter(s)")
else:
    print("ℹ️ No duplicates found")

# Verify syntax
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