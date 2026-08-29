import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_capfix_{ts}")
text = app.read_text(encoding="utf-8")

# Fix: Change words=[] to words=None so pipeline auto-generates captions
old = '        "clips": assets.get("clips") or [],\n        "words": [],'
new = '        "clips": assets.get("clips") or [],\n        "words": None,'

if old in text:
    text = text.replace(old, new)
    print("FIXED: words=None in build_render_kwargs")
    
    app.write_text(text, encoding="utf-8")
    
    try:
        compile(text, "app.py", "exec")
        print("SYNTAX OK")
    except SyntaxError as e:
        print(f"SYNTAX ERROR: {e}")
    
    print(f"Backup: app.py.bak_capfix_{ts}")
    print("Run: streamlit run app.py")
else:
    print("NOT FOUND - searching for words pattern...")
    # Try alternate pattern
    idx = text.find('"clips": assets.get("clips") or [],')
    if idx != -1:
        snippet = text[idx:idx+60]
        print(f"Found at {idx}: {snippet}")
    else:
        print("Clips line not found either")