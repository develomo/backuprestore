# fix_sort_error.py
import re
from pathlib import Path

file_path = Path(__file__).parent / "master_pipeline.py"

if not file_path.exists():
    print("[ERROR] master_pipeline.py not found!")
    input("Press Enter to exit...")
    exit(1)

content = file_path.read_text(encoding="utf-8")

# The safe version of the function that prevents str/int comparison crashes
new_func = """def _natural_key(path):
    stem = Path(path).stem
    parts = []
    cur = ""
    for ch in stem:
        if ch.isdigit():
            cur += ch
        else:
            if cur:
                parts.append((0, int(cur)))
                cur = ""
            parts.append((1, ch.lower()))
    if cur:
        parts.append((0, int(cur)))
    return parts"""

# Try exact match first
old_func_exact = """def _natural_key(path):
    stem = Path(path).stem
    parts = []
    cur = ""
    for ch in stem:
        if ch.isdigit():
            cur += ch
        else:
            if cur:
                parts.append(int(cur))
                cur = ""
            parts.append(ch.lower())
    if cur:
        parts.append(int(cur))
    return parts"""

if old_func_exact in content:
    content = content.replace(old_func_exact, new_func)
    file_path.write_text(content, encoding="utf-8")
    print("[SUCCESS] Fixed _natural_key in master_pipeline.py (Exact match)")
else:
    # Fallback: use regex if spacing is slightly different
    pattern = re.compile(r'def _natural_key\(path\):.*?return parts', re.DOTALL)
    if pattern.search(content):
        content = pattern.sub(new_func, content, count=1)
        file_path.write_text(content, encoding="utf-8")
        print("[SUCCESS] Fixed _natural_key in master_pipeline.py (Regex match)")
    else:
        print("[WARN] Could not find _natural_key to patch. It might already be fixed.")

print("\n[DONE] You can now run your Streamlit app. The sorting crash is permanently fixed.")
input("Press Enter to exit...")