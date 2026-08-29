import shutil, time
from pathlib import Path

BASE = Path(r"D:\My Creation Video Generator\backup")
ts = int(time.time())

app = BASE / "app.py"
shutil.copy2(app, BASE / f"app.py.bak_ovr_{ts}")
text = app.read_text(encoding="utf-8")

# Fix: add custom_overrides = {} before the commented line
old = '# custom_overrides merged into settings section above'
new = 'custom_overrides = {}  # merged into settings section above'

if old in text:
    text = text.replace(old, new)
    print("FIXED: custom_overrides defined")
else:
    print("NOT FOUND - searching...")
    # Try alternate
    old2 = '# custom_overrides merged'
    if old2 in text:
        text = text.replace(old2, 'custom_overrides = {}  # merged')
        print("FIXED (alt)")

app.write_text(text, encoding="utf-8")

try:
    compile(text, "app.py", "exec")
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")

print(f"Backup: app.py.bak_ovr_{ts}")
print("Run: streamlit run app.py")