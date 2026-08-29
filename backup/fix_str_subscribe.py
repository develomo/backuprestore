# fix_str_subscribe.py - PERMANENT FIX for str() + subscribe_overlay issue
from pathlib import Path

app = Path("app.py")
lines = app.read_text(encoding="utf-8").split('\n')

fixed = False

for i in range(len(lines)):
    # Find the exact broken pattern: str(output_file, followed by subscribe_overlay on next line(s)
    if 'output_path=str(output_file,' in lines[i]:
        indent = len(lines[i]) - len(lines[i].lstrip())
        
        # Fix: Close str() properly with ) and add comma
        lines[i] = ' ' * indent + 'output_path=str(output_file),'
        
        # Check next few lines for misplaced params and fix their indentation
        for j in range(i+1, min(i+10, len(lines))):
            stripped = lines[j].strip()
            if stripped and '=' in stripped and not stripped.startswith('#') and not stripped.startswith(')'):
                # Ensure proper indentation (indent + 4 spaces for continuation)
                current_indent = len(lines[j]) - len(lines[j].lstrip())
                expected_indent = indent + 4
                if current_indent != expected_indent:
                    lines[j] = ' ' * expected_indent + stripped
        
        fixed = True
        print(f"✅ FIXED line {i+1}: Closed str(output_file) and fixed param indentation")
        break

if not fixed:
    # Fallback: search across multiple lines
    content = '\n'.join(lines)
    import re
    pattern = r'output_path=str\(output_file,\s*\n(\s+)(subscribe_overlay=|custom_logo_path=|wm_opacity=)'
    match = re.search(pattern, content)
    if match:
        replacement = 'output_path=str(output_file),\n' + ' ' * (len(match.group(1))) + match.group(2)
        content = content.replace(match.group(0), replacement, 1)
        app.write_text(content, encoding="utf-8")
        print("✅ FIXED via regex fallback")
        fixed = True
    else:
        print("⚠️ Could not find broken pattern. Showing relevant lines:")
        for i, line in enumerate(lines):
            if 'str(output_file' in line or 'subscribe_overlay' in line:
                print(f"   Line {i+1}: {line}")

if fixed:
    app.write_text('\n'.join(lines), encoding="utf-8")

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