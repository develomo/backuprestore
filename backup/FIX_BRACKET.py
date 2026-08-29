"""Fix missing closing bracket in _render_video call"""
from pathlib import Path
import shutil, time

APP = Path(r"D:\My Creation Video Generator\backup\app.py")
ts = int(time.time())
shutil.copy2(APP, APP.parent / f"app.py.bak_bracket_{ts}")
text = APP.read_text(encoding="utf-8")
print("=" * 60)
print("FIX: Missing bracket in batch render call")
print("=" * 60)

# Find the broken line
old = 'False,  # mz disabledmp_b'
new = 'False,mp_b'
if old in text:
    text = text.replace(old, new)
    print("[1] Fixed: removed broken comment in _render_video call")
else:
    print("[1] Pattern not found — checking alternatives")
    # Try broader search
    old2 = '# mz disabledmp_b'
    if old2 in text:
        text = text.replace(old2, 'mp_b')
        print("[1b] Alt fix applied")

APP.write_text(text, encoding="utf-8")
print("[2] Written:", len(text), "chars")

try:
    compile(text, "app.py", "exec")
    print("\n✅✅✅ SYNTAX OK! ✅✅✅")
    print("Run: streamlit run app.py")
except SyntaxError as e:
    print(f"\n❌ Line {e.lineno}: {e.msg}")
    L = text.split('\n')
    for ln in range(max(0,e.lineno-3), min(len(L),e.lineno+2)):
        marker = ">>>" if ln+1==e.lineno else "   "
        print(f"  {marker} {ln+1}: {L[ln][:150]}")