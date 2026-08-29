"""
SYNTAX CHECK + AUTO FIX — Run on your PC
"""
import ast, os, sys

APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')

with open(APP_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"[INFO] {len(content.split(chr(10)))} lines")

try:
    ast.parse(content)
    print("\n[OK] Syntax check PASSED! No errors.")
    print("\n▶ RUN: streamlit run app.py")
except SyntaxError as e:
    print(f"\n[FAIL] SyntaxError at line {e.lineno}: {e.msg}")
    lines = content.split('\n')
    lo = max(0, e.lineno - 3)
    hi = min(len(lines), e.lineno + 3)
    for i in range(lo, hi):
        m = ">>>" if i == e.lineno - 1 else "   "
        print(f"  {m} L{i+1}: {lines[i][:140]}")
    
    # Auto-fix: if it's the known indent issue from Fix 7 injection
    if e.lineno and 'kwargs["caption_timing_precision"]' in content:
        # Find and fix the extra indent
        idx = content.find('kwargs["caption_timing_precision"]')
        # Find the next "update(" line
        rest = content[idx:]
        update_idx = rest.find('update(20')
        if update_idx > 0:
            # Get the line with update
            line_start = rest.rfind('\n', 0, update_idx)
            update_line = rest[line_start+1:rest.find('\n', update_idx)]
            stripped = update_line.lstrip()
            if len(update_line) - len(stripped) > 8:
                fixed = '\n        ' + stripped
                old = '\n' + update_line
                content = content.replace(old, fixed)
                with open(APP_PATH, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"\n[AUTO-FIX] Re-indented: {stripped[:60]}")
                try:
                    ast.parse(content)
                    print("[OK] Auto-fix successful!")
                except SyntaxError as e2:
                    print(f"[FAIL] Still broken: {e2}")