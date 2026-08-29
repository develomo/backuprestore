"""
FIX: Add style_id parameter to render_long_batch_memory() in batch_long_renderer.py
This matches the call from safe_long_video_polished.py line 206.
"""
import os, re

BACKUP_DIR = os.path.dirname(os.path.abspath(__file__))
BR_PATH = os.path.join(BACKUP_DIR, 'batch_long_renderer.py')

if not os.path.exists(BR_PATH):
    print(f"[ERROR] {BR_PATH} not found!")
    import sys; sys.exit(1)

with open(BR_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
bak = BR_PATH + '.backup_style_id'
with open(bak, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"[OK] Backup: {bak}")

# Find the exact signature line for "keep_temp=False,"
# style_id should be added BEFORE keep_temp or after temp_root
target = '    keep_temp=False,'
if target in content:
    # Insert style_id parameter before keep_temp
    new_param = '    caption_style_id="auto",\n'
    content = content.replace(target, new_param + target, 1)
    
    # Validate
    try:
        compile(content, BR_PATH, 'exec')
        print("[OK] Syntax check PASSED!")
        with open(BR_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print("[SUCCESS] Added caption_style_id parameter to render_long_batch_memory()")
        print("\n▶ streamlit run app.py")
    except SyntaxError as e:
        print(f"[ERROR] SyntaxError: {e}")
        print("Restoring backup...")
        import shutil
        shutil.copy(bak, BR_PATH)
else:
    print("[ERROR] 'keep_temp=False,' not found - signature may have changed")
    # Try alternate approach: find the closing paren of the function def
    idx = content.find('def render_long_batch_memory')
    if idx >= 0:
        # Find the closing ): of the parameter list
        rest = content[idx:]
        close_paren = rest.find(',\n):')
        if close_paren > 0:
            insert_pos = idx + close_paren
            snippet = content[insert_pos:insert_pos+10]
            print(f"Found closing at {insert_pos}: ...{snippet}...")
            content = content[:insert_pos] + ',\n    caption_style_id="auto"' + content[insert_pos:]
            try:
                compile(content, BR_PATH, 'exec')
                print("[OK] Syntax check PASSED! (alternate method)")
                with open(BR_PATH, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("[SUCCESS] Added caption_style_id parameter")
            except SyntaxError as e:
                print(f"[ERROR] Still broken: {e}")
                import shutil
                shutil.copy(bak, BR_PATH)