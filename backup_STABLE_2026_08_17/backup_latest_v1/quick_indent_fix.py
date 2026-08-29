"""
QUICK PATCH: Fix indent error at line 809 in app.py
"""
import os

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(BACKUP_DIR, 'app.py')

with open(APP_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# The broken line has extra indentation before update()
broken = '        kwargs["caption_timing_precision"] = True\n                update(20, "Loading pipeline")'
fixed = '        kwargs["caption_timing_precision"] = True\n        update(20, "Loading pipeline")'

if broken in content:
    content = content.replace(broken, fixed)
    with open(APP_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print("[OK] Fixed indent on update(20, 'Loading pipeline')")
    try:
        compile(content, APP_PATH, 'exec')
        print("[OK] Syntax check PASSED!")
        print("\n▶ RUN: streamlit run app.py")
    except SyntaxError as e:
        print(f"[FAIL] Still broken: {e}")
else:
    # Try broader search
    if 'kwargs["caption_timing_precision"] = True' in content:
        idx = content.index('kwargs["caption_timing_precision"] = True')
        line_start = content.rfind('\n', 0, idx)
        line_end = content.find('\n', idx)
        print(f"Found at idx {idx}: {content[line_start:line_end]}")
        
        # Replace the next line's indent
        after_line = content[line_end:]
        next_nl = after_line.find('\n', 1)
        if next_nl > 0:
            next_line = after_line[1:next_nl]
            if 'update(20' in next_line:
                fixed_line = next_line.lstrip()
                content = content[:line_end+1] + fixed_line + content[line_end+1+len(next_line):]
                with open(APP_PATH, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("[OK] Fixed via broad search")
                try:
                    compile(content, APP_PATH, 'exec')
                    print("[OK] Syntax check PASSED!")
                except SyntaxError as e:
                    print(f"[FAIL] Still broken: {e}")
    else:
        print("[WARN] Pattern not found in file")